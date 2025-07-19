import * as pdfjs from "pdfjs-dist";
import { useEffect, useRef, useState } from "react";

async function convertBase64ToPDFImages(base64: string) {
  if (!pdfjs.GlobalWorkerOptions.workerSrc) {
    const workerPath = new URL(
      "pdfjs-dist/build/pdf.worker.min.mjs",
      import.meta.url
    );
    pdfjs.GlobalWorkerOptions.workerSrc = workerPath.toString();
  }

  const pdfData = atob(base64);

  const loadingTask = await pdfjs.getDocument({ data: pdfData });
  const pdf = await loadingTask.promise;

  const pages: Array<string> = [];

  async function getPage(pageNumber: number) {
    const page = await pdf.getPage(pageNumber);
    const scale = 3;
    const viewport = page.getViewport({ scale: scale });

    // Prepare canvas using PDF page dimensions
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    // Render PDF page into canvas context
    if (context !== null) {
      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };
      await page.render(renderContext).promise.then(() => {
        const img = canvas.toDataURL("image/png");
        pages.push(img);
      });
    }
  }

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
    await getPage(pageNumber);
  }
  return pages;
}

export function PDFViewer({ pdfBase64 }: { pdfBase64: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [pages, setPages] = useState<HTMLImageElement[]>([]);

  useEffect(() => {
    async function fetchPDFImages() {
      const images = await convertBase64ToPDFImages(
        pdfBase64.slice(pdfBase64.indexOf(",") + 1)
      );
      setPages(
        images.map((base64: string) => {
          const img = new Image();
          img.src = base64;
          return img;
        })
      );
    }
    fetchPDFImages();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas !== null) {
      canvas.width = 800;
      canvas.height = 800;
      const context = canvas.getContext("2d");
      if (context !== null) {
        if (pages.length > 0) {
          context.drawImage(pages[0], 0, 0);
        }
      }
    }
  }, [pages]);

  return (
    <>
      <p>Epic pdf viewer</p>
      <canvas ref={canvasRef} />
    </>
  );
}
