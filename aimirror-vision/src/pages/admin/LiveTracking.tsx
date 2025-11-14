import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getBuses } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Bus, MapPin, Phone } from 'lucide-react';
import GoogleMapComponent from '@/components/GoogleMap';

const AdminLiveTracking: React.FC = () => {
  const [busLocations, setBusLocations] = useState<Map<number, { lat: number; lng: number; timestamp: string }>>(new Map());
  const [selectedBus, setSelectedBus] = useState<number | null>(null);

  const { data: buses } = useQuery({
    queryKey: ['buses'],
    queryFn: getBuses,
  });

  useEffect(() => {
    if (!buses) return;

    // Initialize WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/admin/buses`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'bus_location') {
          setBusLocations((prev) => {
            const newMap = new Map(prev);
            newMap.set(data.bus_id, {
              lat: data.latitude,
              lng: data.longitude,
              timestamp: data.timestamp,
            });
            return newMap;
          });
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [buses]);

  const activeBuses = buses?.filter((bus: any) => bus.is_active && bus.gps_tracker_id) || [];
  const markers = activeBuses
    .map((bus: any) => {
      const location = busLocations.get(bus.id);
      if (!location && bus.gps_tracker?.last_latitude && bus.gps_tracker?.last_longitude) {
        return {
          lat: bus.gps_tracker.last_latitude,
          lng: bus.gps_tracker.last_longitude,
          label: bus.bus_number,
          info: `السائق: ${bus.driver_name}\nالهاتف: ${bus.driver_phone}`,
          busId: bus.id,
        };
      }
      if (location) {
        return {
          lat: location.lat,
          lng: location.lng,
          label: bus.bus_number,
          info: `السائق: ${bus.driver_name}\nالهاتف: ${bus.driver_phone}\nآخر تحديث: ${new Date(location.timestamp).toLocaleString('ar-SA')}`,
          busId: bus.id,
        };
      }
      return null;
    })
    .filter(Boolean);

  const defaultCenter = markers.length > 0 ? { lat: markers[0].lat, lng: markers[0].lng } : { lat: 24.7136, lng: 46.6753 };

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-3xl font-bold">التتبع اللحظي للحافلات</h1>
        <p className="text-muted-foreground mt-2">متابعة مواقع الحافلات في الوقت الفعلي</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>خريطة الحافلات</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden">
              <GoogleMapComponent
                center={defaultCenter}
                zoom={12}
                markers={markers}
                height="600px"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>الحافلات النشطة</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeBuses.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">لا توجد حافلات نشطة</p>
            ) : (
              activeBuses.map((bus: any) => {
                const location = busLocations.get(bus.id);
                const hasLocation = location || (bus.gps_tracker?.last_latitude && bus.gps_tracker?.last_longitude);
                return (
                  <div
                    key={bus.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedBus === bus.id ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
                    }`}
                    onClick={() => setSelectedBus(bus.id)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Bus className="w-5 h-5 text-primary" />
                        <span className="font-bold">{bus.bus_number}</span>
                      </div>
                      <Badge variant={hasLocation ? 'default' : 'secondary'}>
                        {hasLocation ? 'متصل' : 'غير متصل'}
                      </Badge>
                    </div>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4" />
                        <span>{bus.driver_name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4" />
                        <span>{bus.driver_phone}</span>
                      </div>
                      {location && (
                        <div className="text-xs mt-2">
                          آخر تحديث: {new Date(location.timestamp).toLocaleString('ar-SA')}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminLiveTracking;

