import React, { useState, useCallback, useRef } from "react";
import { Excalidraw } from "@excalidraw/excalidraw";
import type { ExcalidrawInitialDataState } from "@excalidraw/excalidraw/types/types";

interface WhiteboardProps {
  initialData?: string;
  onChange?: (dataJson: string) => void;
  viewModeEnabled?: boolean;
  height?: string;
}

export const Whiteboard: React.FC<WhiteboardProps> = ({
  initialData,
  onChange,
  viewModeEnabled = false,
  height = "480px",
}) => {
  // Capture initial state once on mount so subsequent draws don't retrigger initialData re-evaluations
  const [initialState] = useState<ExcalidrawInitialDataState | null>(() => {
    if (!initialData) return null;
    try {
      const parsed = JSON.parse(initialData);
      if (Array.isArray(parsed)) {
        return { elements: parsed, appState: { viewModeEnabled } };
      }
      return {
        elements: parsed.elements || [],
        appState: { ...(parsed.appState || {}), viewModeEnabled },
      };
    } catch {
      return null;
    }
  });

  const lastSerializedRef = useRef<string>("");

  const handleChange = useCallback(
    (elements: readonly any[], appState: any) => {
      if (!onChange || viewModeEnabled) return;

      const nonDeleted = elements ? elements.filter((el) => !el.isDeleted) : [];
      if (nonDeleted.length === 0) {
        if (lastSerializedRef.current !== "") {
          lastSerializedRef.current = "";
          onChange("");
        }
        return;
      }

      const serialized = JSON.stringify({
        elements: nonDeleted,
        appState: {
          viewBackgroundColor: appState?.viewBackgroundColor,
        },
      });

      if (serialized !== lastSerializedRef.current) {
        lastSerializedRef.current = serialized;
        onChange(serialized);
      }
    },
    [onChange, viewModeEnabled]
  );

  return (
    <div
      style={{
        height,
        width: "100%",
        borderRadius: "var(--radius)",
        overflow: "hidden",
        border: "1px solid var(--border)",
        position: "relative",
      }}
    >
      <Excalidraw
        initialData={initialState || undefined}
        onChange={handleChange}
        viewModeEnabled={viewModeEnabled}
        zenModeEnabled={false}
        gridModeEnabled={true}
        UIOptions={{
          canvasActions: {
            changeViewBackgroundColor: true,
            clearCanvas: !viewModeEnabled,
            loadScene: false,
            saveToActiveFile: false,
            toggleTheme: false,
          },
        }}
      />
    </div>
  );
};
