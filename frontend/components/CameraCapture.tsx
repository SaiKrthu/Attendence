"use client";

import { useEffect, useRef, useState } from "react";

export default function CameraCapture({
  onCapture,
  label = "Capture frame",
}: {
  onCapture: (image: string) => void;
  label?: string;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState("");
  const [cameraReady, setCameraReady] = useState(false);

  useEffect(() => {
    let active = true;
    if (!navigator.mediaDevices?.getUserMedia) {
      void Promise.resolve().then(() => {
        if (active) setCameraError("This browser does not support camera access. Try an up-to-date browser on HTTPS.");
      });
      return () => { active = false; };
    }
    navigator.mediaDevices
      .getUserMedia({ audio: false, video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } } })
      .then((stream) => {
        if (!active) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          void videoRef.current.play();
        }
        setCameraReady(true);
      })
      .catch((error: unknown) => {
        if (!active) return;
        const message = error instanceof Error ? error.message : "";
        setCameraError(message.toLowerCase().includes("permission")
          ? "Camera permission was denied. Allow camera access in your browser settings and try again."
          : "Could not start the camera. Check that it is connected and not being used by another app.");
      });
    return () => {
      active = false;
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  function capture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) {
      setCameraError("This browser could not prepare a camera capture.");
      return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    onCapture(canvas.toDataURL("image/jpeg", 0.82));
  }

  return (
    <div className="camera-frame">
      <div className="camera-viewport">
        <video autoPlay className="camera-video" muted playsInline ref={videoRef} />
        {!cameraReady && !cameraError && <div className="camera-overlay">Starting camera…</div>}
        {cameraError && <div className="camera-overlay camera-error">{cameraError}</div>}
        {cameraReady && <span className="camera-live"><i /> CAMERA READY</span>}
        <span className="camera-guide" />
      </div>
      <button className="button-primary camera-button" disabled={!cameraReady} onClick={capture} type="button">{label}</button>
      <p className="camera-hint">Use a well-lit space. Keep one face centered in the frame.</p>
    </div>
  );
}
