declare global {
  interface Window {
    AdobeDC?: {
      View: new (config: {
        clientId: string
        divId: string
      }) => {
        previewFile: (
          content: {
            content: { location: { url: string } }
            metaData: { fileName: string }
          },
          config: {
            enableAnnotationAPIs?: boolean
            includePDFAnnotations?: boolean
            showAnnotationTools?: boolean
            defaultViewMode?: string
            showDownloadPDF?: boolean
            showPrintPDF?: boolean
          }
        ) => void
      }
    }
  }
}

export {}
