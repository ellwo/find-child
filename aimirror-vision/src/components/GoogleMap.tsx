import React, { useCallback, useMemo } from 'react';
import { GoogleMap, useJsApiLoader, Marker, Polyline, InfoWindow } from '@react-google-maps/api';

const libraries: ("drawing" | "geometry" | "localContext" | "places" | "visualization")[] = ['places'];

interface MapLocation {
  lat: number;
  lng: number;
  label?: string;
  info?: string;
  icon?: string | google.maps.Icon; // Custom icon URL or Icon object
  iconType?: 'student' | 'bus' | 'school' | 'default'; // Icon type for default icons
  imageUrl?: string; // For student image
}

interface RoutePoint {
  lat: number;
  lng: number;
  timestamp?: string;
}

interface Route {
  points: RoutePoint[];
  type?: 'entry' | 'exit'; // Route type for color coding
  color?: string; // Custom color override
}

interface GoogleMapComponentProps {
  center: { lat: number; lng: number };
  zoom?: number;
  markers?: MapLocation[];
  route?: RoutePoint[] | Route[]; // Support both single route and multiple routes
  routeType?: 'entry' | 'exit'; // For backward compatibility
  onMarkerClick?: (marker: MapLocation) => void;
  onMapClick?: (e: any) => void;
  height?: string;
}

// Helper function to create custom icon
const createCustomIcon = (type: 'student' | 'bus' | 'school' | 'default', imageUrl?: string): google.maps.Icon | undefined => {
  if (imageUrl && type === 'student') {
    // Use student image as icon
    return {
      url: imageUrl,
      scaledSize: new google.maps.Size(40, 40),
      shape: { coords: [20, 20, 20], type: 'circle' },
    };
  }
  
  // Default icons (using emoji or SVG)
  const iconMap: Record<string, string> = {
    student: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMTJDMTQuNzYxNCAxMiAxNyA5Ljc2MTQyIDE3IDdDMTcgNC4yMzg1OCAxNC43NjE0IDIgMTIgMkM5LjIzODU4IDIgNyA0LjIzODU4IDcgN0M3IDkuNzYxNDIgOS4yMzg1OCAxMiAxMiAxMloiIGZpbGw9IiM0NjY4RjEiLz48cGF0aCBkPSJNMTIgMTRDOC42ODYyOSAxNCA2IDE2LjY4NjMgNiAyMFYyMkgxOFYyMEMxOCAxNi42ODYzIDE1LjMxMzcgMTQgMTIgMTRaIiBmaWxsPSIjNDY2OEYxIi8+PC9zdmc+',
    bus: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTggMTBIMTZWMUgxNFYxMEgxMFYxSDhWMTBINkM0LjkgMTAgNCAxMC45IDQgMTJWMTlIMlYyMUg0VjIySDhWMjFIMTZWMjJIMjBWMjFIMjJWMjlIMjBWMjJIMTZWMjFIOFYyMkg0VjIxSDJWMjFIMlYxOUg0VjEyQzQgMTAuOSA0LjkgMTAgNiAxMEgxOFoiIGZpbGw9IiNGRjY2MDAiLz48L3N2Zz4=',
    school: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkwxIDhMMTIgMTRMMjMgOEwxMiAyWk0xMiAxNkwxIDEwVjIwTDEyIDIyTDIzIDIwVjEwTDEyIDE2WiIgZmlsbD0iIzEwQjk4MSIvPjwvc3ZnPg==',
  };
  
  if (iconMap[type]) {
    return {
      url: iconMap[type],
      scaledSize: new google.maps.Size(40, 40),
    };
  }
  
  return undefined;
};

const GoogleMapComponent: React.FC<GoogleMapComponentProps> = ({
  center,
  zoom = 15,
  markers = [],
  route = [],
  routeType,
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

  // Normalize routes to array of Route objects
  const normalizedRoutes = useMemo(() => {
    if (route.length === 0) return [];
    
    // Check if first item is RoutePoint (has lat/lng) or Route (has points)
    if ('lat' in route[0]) {
      // Single route (backward compatibility)
      return [{
        points: route as RoutePoint[],
        type: routeType || 'entry',
      }];
    } else {
      // Multiple routes
      return route as Route[];
    }
  }, [route, routeType]);

  // Get route color based on type
  const getRouteColor = (type?: 'entry' | 'exit', customColor?: string): string => {
    if (customColor) return customColor;
    if (type === 'entry') return '#10b981'; // Green for entry
    if (type === 'exit') return '#ef4444'; // Red for exit
    return '#3b82f6'; // Default blue
  };

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
      {markers.map((marker, index) => {
        const icon = marker.icon || (marker.iconType ? createCustomIcon(marker.iconType, marker.imageUrl) : undefined);
        return (
          <Marker
            key={`marker-${index}-${marker.lat}-${marker.lng}`}
            position={{ lat: marker.lat, lng: marker.lng }}
            label={marker.label}
            icon={icon}
            onClick={() => handleMarkerClick(marker)}
          />
        );
      })}

      {normalizedRoutes.map((routeItem, routeIndex) => {
        if (routeItem.points.length < 2) return null;
        const routePath = routeItem.points.map((point) => ({ lat: point.lat, lng: point.lng }));
        return (
          <Polyline
            key={`route-${routeIndex}`}
            path={routePath}
            options={{
              strokeColor: getRouteColor(routeItem.type, routeItem.color),
              strokeOpacity: 0.8,
              strokeWeight: 4,
            }}
          />
        );
      })}

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
