import { uploadPhoto } from "./media-api";

export class PhotoUploadError extends Error {
  constructor(
    public fileName: string,
    cause: unknown,
  ) {
    super(`Photo upload failed: ${fileName}`, { cause });
  }
}

// Report each success immediately so a retry only sends unfinished files.
export async function uploadPhotos(
  path: string,
  files: File[],
  onUploaded: () => void,
  fields?: { caption?: string; alt?: string },
) {
  for (const file of files) {
    try {
      await uploadPhoto(path, file, fields);
    } catch (error) {
      throw new PhotoUploadError(file.name, error);
    }
    onUploaded();
  }
}
