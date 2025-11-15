import React, { useCallback, useMemo } from 'react';
import { GoogleMap, useJsApiLoader, Marker, Polyline, InfoWindow } from '@react-google-maps/api';

const libraries: ("drawing" | "geometry" | "localContext" | "places" | "visualization")[] = ['places'];

interface MapLocation {
  lat: number;
  lng: number;
  label?: string;
  info?: string;
}

interface RoutePoint {
  lat: number;
  lng: number;
  timestamp?: string;
}

interface GoogleMapComponentProps {
  center: { lat: number; lng: number };
  zoom?: number;
  markers?: MapLocation[];
  route?: RoutePoint[];
  onMarkerClick?: (marker: MapLocation) => void;
  onMapClick?: (e: any) => void;
  height?: string;
}

const GoogleMapComponent: React.FC<GoogleMapComponentProps> = ({
  center,
  zoom = 15,
  markers = [],
  route = [],
  onMarkerClick,
  onMapClick,
  height = '400px',
}) => {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  const { isLoaded, loadError } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: apiKey,
    libraries,
  });

  const [selectedMarker, setSelectedMarker] = React.useState<MapLocation | null>(null);

  const mapContainerStyle = useMemo(
    () => ({
      width: '100%',
      height: height,
    }),
    [height]
  );

  const handleMarkerClick = useCallback(
    (marker: MapLocation) => {
      setSelectedMarker(marker);
      if (onMarkerClick) {
        onMarkerClick(marker);
      }
    },
    [onMarkerClick]
  );

  const routePath = useMemo(
    () => route.map((point) => ({ lat: point.lat, lng: point.lng })),
    [route]
  );

  const handleMapClick = useCallback(
    (e: google.maps.MapMouseEvent) => {
      if (!onMapClick || !e.latLng) return;
      
      try {
        const lat = e.latLng.lat();
        const lng = e.latLng.lng();
        onMapClick({
          latLng: {
            lat: () => lat,
            lng: () => lng,
          },
        });
      } catch (error) {
        console.error('Error in handleMapClick:', error);
      }
    },
    [onMapClick]
  );

  const mapOptions = useMemo(
    () => ({
      disableDefaultUI: false,
      zoomControl: true,
      streetViewControl: false,
      mapTypeControl: false,
    }),
    []
  );

  if (loadError) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-destructive">خطأ في تحميل Google Maps. يرجى التحقق من API Key.</div>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-muted-foreground">جاري تحميل الخريطة...</div>
      </div>
    );
  }

  if (!apiKey) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-destructive">يرجى إضافة Google Maps API Key</div>
      </div>
    );
  }

  return (
    <GoogleMap 
      mapContainerStyle={mapContainerStyle} 
      center={center} 
      zoom={zoom}
      onClick={onMapClick ? handleMapClick : undefined}
      options={mapOptions}
    >
      {markers.map((marker, index) => (
        <Marker
          key={`marker-${index}-${marker.lat}-${marker.lng}`}
          position={{ lat: marker.lat, lng: marker.lng }}
          label={marker.label}
          onClick={() => handleMarkerClick(marker)}
        />
      ))}

      {route.length > 1 && (
        <Polyline
          path={routePath}
          options={{
            strokeColor: '#3b82f6',
            strokeOpacity: 0.8,
            strokeWeight: 4,
          }}
        />
      )}

      {selectedMarker && (
        <InfoWindow
          position={{ lat: selectedMarker.lat, lng: selectedMarker.lng }}
          onCloseClick={() => setSelectedMarker(null)}
        >
          <div>
            {selectedMarker.label && <h3 className="font-bold">{selectedMarker.label}</h3>}
            {selectedMarker.info && <p className="text-sm">{selectedMarker.info}</p>}
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
  );
};

export default GoogleMapComponent;
