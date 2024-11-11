import React, { useState, useRef, useEffect } from "react";
import { Camera, Upload, FileText, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import "./App.css";


interface DocumentData {
  documentType: "passport" | "driver_license" | "other";
  documentNumber: string;
  fullName: string;
  dateOfBirth?: string;
  dateOfIssue: string;
  dateOfExpiry: string;
  address?: string;
  vehicleTypes?: string[];
  isValid: boolean;
}

interface PreviewData {
  file: File | null;
  previewUrl: string;
}

const DocumentCapture = () => {
  const [documentType, setDocumentType] =
    useState<DocumentData["documentType"]>("passport");
  const [preview, setPreview] = useState<PreviewData>({
    file: null,
    previewUrl: "",
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isInitializingCamera, setIsInitializingCamera] = useState(false);
  const [documentData, setDocumentData] = useState<DocumentData | null>(null);


  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, []);


  useEffect(() => {
    if (isCameraActive && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [isCameraActive]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.type.startsWith("image/")) {
        setPreview({
          file,
          previewUrl: URL.createObjectURL(file),
        });
        setError("");
      } else {
        setError("Please upload an image file");
      }
    }
  };

  const startCamera = async () => {
    if (isInitializingCamera) return; 
    setIsInitializingCamera(true);
    setError("");

    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      console.log("Requesting camera access...");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "environment",
        },
      });

      console.log("Camera access granted");
      streamRef.current = stream;
      setIsCameraActive(true);
    } catch (err) {
      console.error("Camera error:", err);
      if (err instanceof Error) {
        switch (err.name) {
          case "NotAllowedError":
          case "PermissionDeniedError":
            setError(
              "Camera access denied. Please allow camera access in your browser settings."
            );
            break;
          case "NotFoundError":
          case "DevicesNotFoundError":
            setError("No camera found on your device.");
            break;
          case "NotReadableError":
          case "TrackStartError":
            setError("Camera is already in use by another application.");
            break;
          default:
            setError(`Camera error: ${err.message}`);
        }
      } else {
        setError("An unexpected error occurred while accessing the camera");
      }
    } finally {
      setIsInitializingCamera(false);
    }
  };

  const captureImage = () => {
    if (!videoRef.current || !streamRef.current) {
      setError("Camera not properly initialized");
      return;
    }

    try {
      const canvas = document.createElement("canvas");
      const video = videoRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");

      if (!ctx) {
        throw new Error("Could not get canvas context");
      }

      ctx.drawImage(video, 0, 0);
      canvas.toBlob(
        (blob) => {
          if (blob) {
            const file = new File([blob], "captured-document.jpg", {
              type: "image/jpeg",
            });
            setPreview({
              file,
              previewUrl: URL.createObjectURL(blob),
            });
            stopCamera();
          } else {
            throw new Error("Failed to create image blob");
          }
        },
        "image/jpeg",
        0.95
      );
    } catch (err) {
      console.error("Capture error:", err);
      setError("Failed to capture image");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  };

  const processDocument = async () => {
    if (!preview.file) {
      setError("Please capture or upload a document first");
      return;
    }

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append("file", preview.file);
      formData.append("documentType", documentType);

      const response = await fetch(
        "http://localhost:8000/api/process-document/",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Failed to process document");
      }

      const data = await response.json();

      setDocumentData(data);
    } catch (error) {
      setError("Failed to process document");
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Document Capture</h2>

        <div className="space-y-2">
          <label className="block text-sm font-medium">Document Type</label>
          <select
            className="w-full p-2 border rounded-md text-white"
            value={documentType}
            onChange={(e) =>
              setDocumentType(e.target.value as DocumentData["documentType"])
            }
          >
            <option value="passport">Passport</option>
            <option value="driver_license">Driver's License</option>
            <option value="other">Other Government ID</option>
          </select>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex gap-4">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Upload className="w-4 h-4" />
            Upload
          </button>

          <button
            onClick={isCameraActive ? captureImage : startCamera}
            disabled={isInitializingCamera}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-green-400"
          >
            <Camera className="w-4 h-4" />
            {isInitializingCamera
              ? "Initializing..."
              : isCameraActive
              ? "Capture"
              : "Use Camera"}
          </button>

          {isCameraActive && (
            <button
              onClick={stopCamera}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Stop Camera
            </button>
          )}
        </div>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/*"
          className="hidden"
        />

        {isCameraActive ? (
          <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              onLoadedMetadata={() => {
                if (videoRef.current) {
                  videoRef.current.play().catch((err) => {
                    console.error("Error playing video:", err);
                    setError("Failed to start video preview");
                  });
                }
              }}
              className="w-full h-full object-cover"
            />
          </div>
        ) : (
          preview.previewUrl && (
            <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
              <img
                src={preview.previewUrl}
                alt="Document preview"
                className="w-full h-full object-contain"
              />
            </div>
          )
        )}

        {preview.file && (
          <button
            onClick={processDocument}
            disabled={isProcessing}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400"
          >
            <FileText className="w-4 h-4" />
            {isProcessing ? "Processing..." : "Process Document"}
          </button>
        )}
      </div>
      {documentData && (
        <div className="bg-gray-100 p-4 rounded-md shadow-md">
          <h3 className="text-lg font-semibold">Extracted Document Details</h3>
          <ul className="text-sm space-y-2">
            <li>
              <strong>Document Type:</strong> {documentData.documentType}
            </li>
            <li>
              <strong>Document Number:</strong> {documentData.documentNumber}
            </li>
            <li>
              <strong>Full Name:</strong> {documentData.fullName}
            </li>
            <li>
              <strong>Date of Birth:</strong> {documentData.dateOfBirth}
            </li>
            <li>
              <strong>Date of Issue:</strong> {documentData.dateOfIssue}
            </li>
            <li>
              <strong>Date of Expiry:</strong> {documentData.dateOfExpiry}
            </li>
            <li>
              <strong>Address:</strong> {documentData.address}
            </li>
            <li>
              <strong>Valid:</strong> {documentData.isValid ? "Yes" : "No"}
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default DocumentCapture;
