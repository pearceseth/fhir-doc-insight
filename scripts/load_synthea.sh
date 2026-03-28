#!/bin/sh

# Synthea FHIR bundle loader for HAPI FHIR server
# Runs once on first startup, skips on subsequent runs

MARKER_FILE="/synthea-data/.loaded"
FHIR_URL="http://hapi-fhir:8080/fhir"
DATA_DIR="/synthea-data"
PATIENT_LIMIT="${PATIENT_LIMIT:-0}"  # 0 = unlimited

# Check if already loaded
if [ -f "$MARKER_FILE" ]; then
    echo "Synthea data already loaded (marker file exists). Skipping."
    exit 0
fi

# Wait for HAPI FHIR to be ready
echo "Waiting for HAPI FHIR to be ready..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$FHIR_URL/metadata")
    if [ "$status" = "200" ]; then
        echo "HAPI FHIR is ready."
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts: HAPI FHIR not ready (status: $status). Retrying in 5s..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo "Error: HAPI FHIR did not become ready after $max_attempts attempts."
    exit 1
fi

# Initialize counters
loaded=0
failed=0

# Function to load a single bundle
load_bundle() {
    file="$1"
    filename=$(basename "$file")
    status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$FHIR_URL" \
        -H "Content-Type: application/fhir+json" \
        --data-binary "@$file")

    if [ "$status" = "200" ] || [ "$status" = "201" ]; then
        loaded=$((loaded + 1))
        echo "Loaded: $filename"
        sleep 1
        return 0
    else
        failed=$((failed + 1))
        echo "Warning: $filename failed with status $status"
        return 1
    fi
}

# Phase 1: Load hospital and practitioner information first (required dependencies)
echo "=== Phase 1: Loading reference data (hospitals, practitioners) ==="
for file in "$DATA_DIR"/hospitalInformation*.json "$DATA_DIR"/practitionerInformation*.json; do
    [ -e "$file" ] || continue
    load_bundle "$file"
done

# Phase 2: Load patient bundles
echo "=== Phase 2: Loading patient data ==="
if [ "$PATIENT_LIMIT" -gt 0 ]; then
    echo "Patient limit: $PATIENT_LIMIT"
fi
patient_count=0
for file in "$DATA_DIR"/*.json; do
    [ -e "$file" ] || continue
    filename=$(basename "$file")
    # Skip already-loaded reference files
    case "$filename" in
        hospitalInformation*|practitionerInformation*) continue ;;
    esac
    # Check patient limit
    if [ "$PATIENT_LIMIT" -gt 0 ] && [ "$patient_count" -ge "$PATIENT_LIMIT" ]; then
        echo "Patient limit reached ($PATIENT_LIMIT). Stopping."
        break
    fi
    load_bundle "$file"
    patient_count=$((patient_count + 1))
done

# Write marker file
touch "$MARKER_FILE"

# Print summary
echo "Done. Loaded: $loaded, Failed: $failed"

exit 0
