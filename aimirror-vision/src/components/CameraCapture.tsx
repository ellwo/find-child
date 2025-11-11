import { useRef, useState, useEffect } from 'react';
import { Camera, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTranslation } from 'react-i18next';

interface CameraCaptureProps {
  onCapture: (blob: Blob) => void;
  onClose: () => void;
}

export const CameraCapture = ({ onCapture, onClose }: CameraCaptureProps) => {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setIsLoading(false);
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError(t('camera.error'));
      setIsLoading(false);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const context = canvas.getContext('2d');
      if (context) {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob((blob) => {
          if (blob) {
            onCapture(blob);
            stopCamera();
          }
        }, 'image/jpeg', 0.95);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full h-full flex flex-col">
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 z-20 p-4 flex justify-between items-center glass-effect">
          <h3 className="text-lg font-semibold">{t('camera.title')}</h3>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="rounded-full"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Camera View */}
        <div className="flex-1 relative flex items-center justify-center overflow-hidden bg-black">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
              <div className="text-center">
                <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary" />
                <p className="text-muted-foreground">{t('camera.loading')}</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
              <div className="text-center p-6">
                <Camera className="w-12 h-12 mx-auto mb-4 text-destructive" />
                <p className="text-destructive mb-4">{error}</p>
                <Button onClick={startCamera} variant="outline">
                  {t('camera.retry')}
                </Button>
              </div>
            </div>
          )}

          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />

          {/* Framing Guide - Square Overlay */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="relative w-[85%] max-w-md aspect-square">
              {/* Corner decorations */}
              <div className="absolute -top-1 -left-1 w-12 h-12 border-t-4 border-l-4 border-primary animate-glow-pulse rounded-tl-2xl" />
              <div className="absolute -top-1 -right-1 w-12 h-12 border-t-4 border-r-4 border-primary animate-glow-pulse rounded-tr-2xl" />
              <div className="absolute -bottom-1 -left-1 w-12 h-12 border-b-4 border-l-4 border-primary animate-glow-pulse rounded-bl-2xl" />
              <div className="absolute -bottom-1 -right-1 w-12 h-12 border-b-4 border-r-4 border-primary animate-glow-pulse rounded-br-2xl" />
              
              {/* Center guide lines */}
              <div className="absolute top-1/2 left-0 right-0 h-[2px] bg-primary/30 -translate-y-1/2" />
              <div className="absolute left-1/2 top-0 bottom-0 w-[2px] bg-primary/30 -translate-x-1/2" />
              
              {/* Instruction text */}
              <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 text-center">
                <p className="text-white text-sm font-medium px-4 py-2 rounded-full glass-effect shadow-glow">
                  {t('camera.instruction')}
                </p>
              </div>
            </div>
          </div>

          <canvas ref={canvasRef} className="hidden" />
        </div>

        {/* Controls */}
        <div className="absolute bottom-0 left-0 right-0 z-20 p-8 glass-effect">
          <div className="flex justify-center items-center gap-4">
            <Button
              onClick={capturePhoto}
              disabled={isLoading || !!error}
              size="lg"
              className="w-20 h-20 rounded-full gradient-primary shadow-glow hover:scale-110 transition-bounce"
            >
              <Camera className="w-8 h-8" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
