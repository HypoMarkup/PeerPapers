import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { create, fromBinary, toBinary } from "@bufbuild/protobuf";
import {
  AuthenticateSchema,
  ClientMessage,
  ClientMessageSchema,
  CreateRoomSchema,
  ForceEndPhaseSchema,
  JoinRoomSchema,
  LeaveRoomSchema,
  MarkingAssignment,
  RequestExamPdfSchema,
  SaveProgressSchema,
  ServerMessageSchema,
  SetReadySchema,
  StartExamSchema,
  SubmitMarkingSchema,
  UpdateSettingsSchema,
  UploadExamSchema,
} from "../generated/v1/messages_pb";
import {
  MarkingResultSchema,
  PlayerResult,
  RoomSettingsSchema,
  RoomSnapshot,
  SectionFeedbackSchema,
  SubmissionSectionSchema,
} from "../generated/v1/models_pb";

interface WebSocketContextType {
  isConnected: boolean;
  sessionToken: string | null;
  playerId: string | null;
  roomCode: string | null;
  snapshot: RoomSnapshot | null;
  pdfBlobUrl: string | null;
  pdfFilename: string | null;
  assignedPaper: MarkingAssignment | null;
  results: PlayerResult[];
  errorMessage: string | null;
  clearError: () => void;
  createRoom: (playerName: string, password: string, durationMins: number) => void;
  joinRoom: (roomCode: string, playerName: string, password: string) => void;
  leaveRoom: () => void;
  updateSettings: (durationMins: number) => void;
  setReady: (isReady: boolean) => void;
  uploadExam: (filename: string, fileBytes: Uint8Array) => void;
  startExam: () => void;
  saveProgress: (sectionIndex: number, textData: string, whiteboardData?: string) => void;
  requestExamPdf: () => void;
  submitMarking: (sections: { sectionIndex: number; score: number; maxScore: number; textComments: string; whiteboardAnnotations?: string }[]) => void;
  forceEndPhase: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8765";

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionToken, setSessionToken] = useState<string | null>(() => localStorage.getItem("peerpapers_token"));
  const [playerId, setPlayerId] = useState<string | null>(null);
  const [roomCode, setRoomCode] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<RoomSnapshot | null>(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfFilename, setPdfFilename] = useState<string | null>(null);
  const [assignedPaper, setAssignedPaper] = useState<MarkingAssignment | null>(null);
  const [results, setResults] = useState<PlayerResult[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const clearError = useCallback(() => setErrorMessage(null), []);

  const send = useCallback((msg: ClientMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const bytes = toBinary(ClientMessageSchema, msg);
      wsRef.current.send(bytes);
    } else {
      setErrorMessage("Not connected to the server.");
    }
  }, []);

  // Connect WebSocket
  useEffect(() => {
    let isUnmounted = false;
    const ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      if (isUnmounted) return;
      setIsConnected(true);
      setErrorMessage(null); // Clear any connection errors on success

      // Auto-reconnect if session token exists
      const savedToken = localStorage.getItem("peerpapers_token");
      if (savedToken) {
        const authMsg = create(ClientMessageSchema, {
          payload: {
            case: "authenticate",
            value: create(AuthenticateSchema, { sessionToken: savedToken }),
          },
        });
        ws.send(toBinary(ClientMessageSchema, authMsg));
      }
    };

    ws.onclose = () => {
      if (isUnmounted) return;
      setIsConnected(false);
    };

    ws.onerror = () => {
      if (isUnmounted) return;
      setIsConnected(false);
      setErrorMessage("WebSocket connection error. Please check if the backend server is running.");
    };

    ws.onmessage = (event: MessageEvent<ArrayBuffer>) => {
      try {
        const rawData = new Uint8Array(event.data);
        const serverMsg = fromBinary(ServerMessageSchema, rawData);

        switch (serverMsg.payload.case) {
          case "authSuccess": {
            const token = serverMsg.payload.value.sessionToken;
            const pid = serverMsg.payload.value.playerId;
            setSessionToken(token);
            setPlayerId(pid);
            localStorage.setItem("peerpapers_token", token);
            break;
          }

          case "roomCreated": {
            setRoomCode(serverMsg.payload.value.roomCode);
            break;
          }

          case "roomStateUpdate": {
            const snap = serverMsg.payload.value.room;
            if (snap) {
              setSnapshot(snap);
              setRoomCode(snap.roomCode);
            }
            break;
          }

          case "markingAssignment": {
            setAssignedPaper(serverMsg.payload.value);
            break;
          }

          case "resultsBroadcast": {
            setResults(serverMsg.payload.value.results);
            break;
          }

          case "examPdfContent": {
            const { filename, fileData } = serverMsg.payload.value;
            const blob = new Blob([fileData as unknown as BlobPart], { type: "application/pdf" });
            const url = URL.createObjectURL(blob);
            setPdfBlobUrl(url);
            setPdfFilename(filename);
            break;
          }

          case "error": {
            setErrorMessage(serverMsg.payload.value.message);
            break;
          }
        }
      } catch (e) {
        console.error("Failed to decode Protobuf ServerMessage:", e);
      }
    };

    return () => {
      isUnmounted = true;
      ws.close();
    };
  }, []);

  // Handler functions
  const createRoom = useCallback((playerName: string, password: string, durationMins: number) => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "createRoom",
        value: create(CreateRoomSchema, {
          playerName,
          password,
          settings: create(RoomSettingsSchema, { examDurationMins: durationMins }),
        }),
      },
    });
    send(msg);
  }, [send]);

  const joinRoom = useCallback((code: string, playerName: string, password: string) => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "joinRoom",
        value: create(JoinRoomSchema, {
          roomCode: code,
          playerName,
          password,
        }),
      },
    });
    send(msg);
  }, [send]);

  const leaveRoom = useCallback(() => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "leaveRoom",
        value: create(LeaveRoomSchema, {}),
      },
    });
    send(msg);
    localStorage.removeItem("peerpapers_token");
    setSessionToken(null);
    setPlayerId(null);
    setRoomCode(null);
    setSnapshot(null);
    setAssignedPaper(null);
    setResults([]);
  }, [send]);

  const updateSettings = useCallback((durationMins: number) => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "updateSettings",
        value: create(UpdateSettingsSchema, {
          settings: create(RoomSettingsSchema, { examDurationMins: durationMins }),
        }),
      },
    });
    send(msg);
  }, [send]);

  const setReady = useCallback((isReady: boolean) => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "setReady",
        value: create(SetReadySchema, { isReady }),
      },
    });
    send(msg);
  }, [send]);

  const uploadExam = useCallback((filename: string, fileBytes: Uint8Array) => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "uploadExam",
        value: create(UploadExamSchema, {
          filename,
          fileData: fileBytes,
        }),
      },
    });
    send(msg);
  }, [send]);

  const startExam = useCallback(() => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "startExam",
        value: create(StartExamSchema, {}),
      },
    });
    send(msg);
  }, [send]);

  const saveProgress = useCallback((sectionIndex: number, textData: string, whiteboardData: string = "") => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "saveProgress",
        value: create(SaveProgressSchema, {
          section: create(SubmissionSectionSchema, {
            sectionIndex,
            textData,
            whiteboardData,
          }),
        }),
      },
    });
    send(msg);
  }, [send]);

  const requestExamPdf = useCallback(() => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "requestExamPdf",
        value: create(RequestExamPdfSchema, {}),
      },
    });
    send(msg);
  }, [send]);

  const submitMarking = useCallback(
    (sections: { sectionIndex: number; score: number; maxScore: number; textComments: string; whiteboardAnnotations?: string }[]) => {
      const feedbackList = sections.map((s) =>
        create(SectionFeedbackSchema, {
          sectionIndex: s.sectionIndex,
          score: s.score,
          maxScore: s.maxScore,
          textComments: s.textComments,
          whiteboardAnnotations: s.whiteboardAnnotations || "",
        })
      );

      const msg = create(ClientMessageSchema, {
        payload: {
          case: "submitMarking",
          value: create(SubmitMarkingSchema, {
            result: create(MarkingResultSchema, {
              sections: feedbackList,
            }),
          }),
        },
      });
      send(msg);
    },
    [send]
  );

  const forceEndPhase = useCallback(() => {
    const msg = create(ClientMessageSchema, {
      payload: {
        case: "forceEndPhase",
        value: create(ForceEndPhaseSchema, {}),
      },
    });
    send(msg);
  }, [send]);

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        sessionToken,
        playerId,
        roomCode,
        snapshot,
        pdfBlobUrl,
        pdfFilename,
        assignedPaper,
        results,
        errorMessage,
        clearError,
        createRoom,
        joinRoom,
        leaveRoom,
        updateSettings,
        setReady,
        uploadExam,
        startExam,
        saveProgress,
        requestExamPdf,
        submitMarking,
        forceEndPhase,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
};
