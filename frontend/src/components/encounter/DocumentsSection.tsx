import type { DocumentReference } from "@/api/fhir";

interface DocumentsSectionProps {
  documents: DocumentReference[];
}

function getTypeDisplay(doc: DocumentReference): string {
  if (doc.type?.text) return doc.type.text;
  if (doc.type?.coding && doc.type.coding.length > 0) {
    return doc.type.coding[0].display || doc.type.coding[0].code || "Unknown";
  }
  return "Document";
}

function formatDate(dateString?: string): string {
  if (!dateString) return "";
  try {
    return new Date(dateString).toLocaleDateString();
  } catch {
    return dateString;
  }
}

function getContentTypeLabel(contentType?: string): string {
  if (!contentType) return "";
  const typeMap: Record<string, string> = {
    "text/plain": "Plain Text",
    "text/html": "HTML",
    "application/pdf": "PDF",
    "image/jpeg": "JPEG Image",
    "image/png": "PNG Image",
    "application/dicom": "DICOM",
  };
  return typeMap[contentType] || contentType;
}

export function DocumentsSection({ documents }: DocumentsSectionProps) {
  if (documents.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">No documents available</div>
    );
  }

  return (
    <ul className="space-y-3">
      {documents.map((doc) => {
        const attachments = doc.content?.map((c) => c.attachment).filter(Boolean) || [];
        const hasAttachments = attachments.length > 0;

        return (
          <li key={doc.id} className="text-sm border rounded-md p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-medium">{getTypeDisplay(doc)}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-muted capitalize">
                {doc.status}
              </span>
            </div>

            {hasAttachments && (
              <div className="space-y-1">
                {attachments.map((attachment, idx) => (
                  <div key={idx} className="text-muted-foreground">
                    {attachment?.title && (
                      <div className="flex items-center gap-2">
                        {attachment.url ? (
                          <a
                            href={attachment.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline"
                          >
                            {attachment.title}
                          </a>
                        ) : (
                          <span>{attachment.title}</span>
                        )}
                        {attachment.contentType && (
                          <span className="text-xs text-muted-foreground">
                            ({getContentTypeLabel(attachment.contentType)})
                          </span>
                        )}
                      </div>
                    )}
                    {!attachment?.title && attachment?.contentType && (
                      <span className="text-xs">
                        {getContentTypeLabel(attachment.contentType)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {doc.date && (
              <div className="text-xs text-muted-foreground">
                {formatDate(doc.date)}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
