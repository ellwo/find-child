import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import {
  getMyStudent,
  getLastAttendance,
  getAttendanceHistory,
  getBusLocation,
  getRouteHistory,
  getRouteByAttendance,
} from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, MapPin, Clock, UserCheck, Bus, Phone } from 'lucide-react';
import { format } from 'date-fns';
import { ar } from 'date-fns/locale';
import GoogleMapComponent from '@/components/GoogleMap';

const ParentStudentTracking: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isParent } = useAuth();
  const studentId = parseInt(id || '0');

  const [busLocation, setBusLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [entryRoute, setEntryRoute] = useState<any[]>([]);
  const [exitRoute, setExitRoute] = useState<any[]>([]);

  const { data: student, isLoading: studentLoading } = useQuery({
    queryKey: ['student', studentId],
    queryFn: () => getMyStudent(studentId),
    enabled: !!studentId && isParent,
  });

  const { data: lastAttendance } = useQuery({
    queryKey: ['last-attendance', studentId],
    queryFn: () => getLastAttendance(studentId),
    enabled: !!studentId && isParent,
  });

  const { data: attendanceHistory } = useQuery({
    queryKey: ['attendance-history', studentId],
    queryFn: () => getAttendanceHistory(studentId),
    enabled: !!studentId && isParent,
  });

  const { data: busLocationData, refetch: refetchBusLocation } = useQuery({
    queryKey: ['bus-location', studentId],
    queryFn: () => getBusLocation(studentId),
    enabled: !!studentId && isParent && !!student?.bus_id,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  useEffect(() => {
    if (busLocationData?.location?.latitude && busLocationData?.location?.longitude) {
      setBusLocation({
        lat: busLocationData.location.latitude,
        lng: busLocationData.location.longitude,
      });
    }
  }, [busLocationData]);

  useEffect(() => {
    if (studentId && student?.bus_id) {
      // Get entry route
      getRouteHistory(studentId, {
        attendance_type: 'entry',
      }).then((data) => {
        if (data.route_points) {
          setEntryRoute(data.route_points);
        }
      }).catch(() => {
        setEntryRoute([]);
      });

      // Get exit route
      getRouteHistory(studentId, {
        attendance_type: 'exit',
      }).then((data) => {
        if (data.route_points) {
          setExitRoute(data.route_points);
        }
      }).catch(() => {
        setExitRoute([]);
      });
    }
  }, [studentId, student?.bus_id]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!studentId || !busLocationData?.is_active_time) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/parent/${studentId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'student_bus_location') {
          setBusLocation({
            lat: data.latitude,
            lng: data.longitude,
          });
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    return () => {
      ws.close();
    };
  }, [studentId, busLocationData?.is_active_time]);

  if (!isParent) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">ليس لديك صلاحية للوصول إلى هذه الصفحة</p>
      </div>
    );
  }

  if (studentLoading) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">جاري التحميل...</p>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">الطالب غير موجود</p>
        <Button onClick={() => navigate('/parent/dashboard')} className="mt-4">
          العودة
        </Button>
      </div>
    );
  }

  const mapCenter = busLocation || (student.home_latitude && student.home_longitude
    ? { lat: student.home_latitude, lng: student.home_longitude }
    : { lat: 24.7136, lng: 46.6753 });

  // Get school location from settings (if available)
  const schoolLocation = { lat: 24.7136, lng: 46.6753 }; // Default, should be from settings

  const markers = [];
  if (busLocation) {
    markers.push({
      lat: busLocation.lat,
      lng: busLocation.lng,
      label: 'الحافلة',
      info: `الحافلة: ${student.bus?.bus_number || ''}`,
      iconType: 'bus' as const,
    });
  }
  if (student.home_latitude && student.home_longitude) {
    markers.push({
      lat: student.home_latitude,
      lng: student.home_longitude,
      label: student.name,
      info: 'منزل الطالب',
      iconType: 'student' as const,
      imageUrl: student.image_url,
    });
  }
  // Add school marker
  markers.push({
    lat: schoolLocation.lat,
    lng: schoolLocation.lng,
    label: 'المدرسة',
    info: 'المدرسة',
    iconType: 'school' as const,
  });

  // Prepare routes with types
  const routes = [];
  if (entryRoute.length > 0) {
    routes.push({
      points: entryRoute.map((point: any) => ({
        lat: point.latitude,
        lng: point.longitude,
      })),
      type: 'entry' as const,
    });
  }
  if (exitRoute.length > 0) {
    routes.push({
      points: exitRoute.map((point: any) => ({
        lat: point.latitude,
        lng: point.longitude,
      })),
      type: 'exit' as const,
    });
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/parent/dashboard')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          العودة
        </Button>
        <div className="flex items-center gap-4">
          {student.image_url ? (
            <img 
              src={student.image_url} 
              alt={student.name}
              className="w-16 h-16 rounded-full object-cover border-2 border-primary"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-gradient-accent flex items-center justify-center">
              <UserCheck className="w-8 h-8 text-white" />
            </div>
          )}
          <div>
            <h1 className="text-3xl font-bold">{student.name}</h1>
            <p className="text-muted-foreground mt-2">متابعة النشاط والموقع</p>
          </div>
        </div>
      </div>

      <Tabs defaultValue="location" className="space-y-4">
        <TabsList>
          <TabsTrigger value="location">الموقع</TabsTrigger>
          <TabsTrigger value="attendance">الحضور</TabsTrigger>
          <TabsTrigger value="history">السجل</TabsTrigger>
        </TabsList>

        <TabsContent value="location" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>موقع الحافلة</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {student.bus ? (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">رقم الحافلة</p>
                      <p className="font-semibold">{student.bus.bus_number}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">اسم السائق</p>
                      <p className="font-semibold">{student.bus.driver_name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">رقم هاتف السائق</p>
                      <p className="font-semibold">{student.bus.driver_phone}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">حالة التتبع</p>
                      <Badge variant={busLocationData?.tracker_active ? 'default' : 'secondary'}>
                        {busLocationData?.tracker_active ? 'نشط' : 'غير نشط'}
                      </Badge>
                    </div>
                  </div>

                  {busLocationData?.is_active_time && (
                    <div className="mt-4">
                      <Badge variant="default" className="mb-2">
                        التتبع اللحظي مفعل
                      </Badge>
                    </div>
                  )}
                  {!busLocationData?.is_active_time && (
                    <div className="mt-4">
                      <Badge variant="secondary" className="mb-2">
                        التتبع اللحظي معطل (يرجى تفعيل WebSocket من الإعدادات)
                      </Badge>
                    </div>
                  )}

                  {busLocation && (
                    <div className="border rounded-lg overflow-hidden">
                      <GoogleMapComponent
                        center={mapCenter}
                        zoom={15}
                        markers={markers}
                        route={routes.length > 0 ? routes : undefined}
                        height="400px"
                      />
                    </div>
                  )}

                  {!busLocation && (
                    <div className="text-center py-8 text-muted-foreground">
                      لا يوجد موقع متاح للحافلة حالياً
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  الطالب غير مرتبط بحافلة
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="attendance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>آخر حضور</CardTitle>
            </CardHeader>
            <CardContent>
              {lastAttendance ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">وقت الحضور</p>
                      <p className="font-semibold">
                        {format(new Date(lastAttendance.detected_at), 'PPp', { locale: ar })}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">نسبة التطابق</p>
                      <p className="font-semibold">
                        {(lastAttendance.similarity_score * 100).toFixed(1)}%
                      </p>
                    </div>
                    {lastAttendance.gps_latitude && lastAttendance.gps_longitude && (
                      <div className="col-span-2">
                        <p className="text-sm text-muted-foreground mb-2">موقع الحضور</p>
                        <div className="border rounded-lg overflow-hidden">
                          <GoogleMapComponent
                            center={{
                              lat: lastAttendance.gps_latitude,
                              lng: lastAttendance.gps_longitude,
                            }}
                            zoom={15}
                            markers={[
                              {
                                lat: lastAttendance.gps_latitude,
                                lng: lastAttendance.gps_longitude,
                                label: 'موقع الحضور',
                              },
                            ]}
                            height="200px"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  لا يوجد سجل حضور
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>سجل الحضور</CardTitle>
            </CardHeader>
            <CardContent>
              {attendanceHistory?.items?.length > 0 ? (
                <div className="space-y-4">
                  {attendanceHistory.items.map((attendance: any) => (
                    <div key={attendance.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <UserCheck className="w-5 h-5 text-primary" />
                          <div>
                            <p className="font-semibold">
                              {format(new Date(attendance.detected_at), 'PPp', { locale: ar })}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              نسبة التطابق: {(attendance.similarity_score * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        {attendance.gps_latitude && attendance.gps_longitude && (
                          <Badge variant="outline">
                            <MapPin className="w-3 h-3 mr-1" />
                            موقع متاح
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  لا يوجد سجل حضور
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ParentStudentTracking;

