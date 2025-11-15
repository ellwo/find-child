import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import {
  getStudentTracking,
  getStudentAttendanceHistory,
  getStudents,
  getRouteHistory,
  getStudentRoutes,
} from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ArrowLeft, MapPin, Clock, UserCheck, Bus, Phone, Filter, Image as ImageIcon } from 'lucide-react';
import { format } from 'date-fns';
import { ar } from 'date-fns/locale';
import GoogleMapComponent from '@/components/GoogleMap';

const AdminStudentTracking: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(id ? parseInt(id) : null);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    bus_id: '',
  });

  const [busLocation, setBusLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [entryRoute, setEntryRoute] = useState<any[]>([]);
  const [exitRoute, setExitRoute] = useState<any[]>([]);

  // Get all students for dropdown
  const { data: students } = useQuery({
    queryKey: ['all-students'],
    queryFn: () => getStudents(),
    enabled: isAdmin,
  });

  // Get tracking data
  const { data: trackingData, isLoading: trackingLoading } = useQuery({
    queryKey: ['admin-tracking', selectedStudentId],
    queryFn: () => getStudentTracking(selectedStudentId!),
    enabled: !!selectedStudentId && isAdmin,
  });

  // Get attendance history with filters
  const { data: attendanceHistory, refetch: refetchHistory } = useQuery({
    queryKey: ['admin-attendance-history', selectedStudentId, filters],
    queryFn: () => getStudentAttendanceHistory(selectedStudentId!, {
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
      bus_id: filters.bus_id ? parseInt(filters.bus_id) : undefined,
    }),
    enabled: !!selectedStudentId && isAdmin,
  });

  useEffect(() => {
    if (id) {
      setSelectedStudentId(parseInt(id));
    }
  }, [id]);

  useEffect(() => {
    if (trackingData?.location?.latitude && trackingData?.location?.longitude) {
      setBusLocation({
        lat: trackingData.location.latitude,
        lng: trackingData.location.longitude,
      });
    }
  }, [trackingData]);

  useEffect(() => {
    if (selectedStudentId && trackingData?.student?.bus_id) {
      // Get routes using new API
      getStudentRoutes(selectedStudentId).then((data) => {
        if (data.entry?.route_points) {
          setEntryRoute(data.entry.route_points);
        }
        if (data.exit?.route_points) {
          setExitRoute(data.exit.route_points);
        }
      }).catch((err) => {
        console.error('Error fetching routes:', err);
        setEntryRoute([]);
        setExitRoute([]);
      });
    }
  }, [selectedStudentId, trackingData?.student?.bus_id]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!selectedStudentId || !trackingData?.is_active_time) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/parent/${selectedStudentId}`;
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
  }, [selectedStudentId, trackingData?.is_active_time]);

  if (!isAdmin) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">ليس لديك صلاحية للوصول إلى هذه الصفحة</p>
      </div>
    );
  }

  const student = trackingData?.student;
  const lastAttendance = trackingData?.last_attendance;
  const bus = trackingData?.bus;

  const mapCenter = busLocation || (student?.home_latitude && student?.home_longitude
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
      info: `الحافلة: ${bus?.bus_number || ''}`,
      iconType: 'bus' as const,
    });
  }
  if (student?.home_latitude && student?.home_longitude) {
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

  const handleFilterChange = () => {
    refetchHistory();
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/admin/students')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          العودة
        </Button>
        <div className="flex-1 flex items-center gap-4">
          {student?.image_url ? (
            <img 
              src={student.image_url} 
              alt={student.name}
              className="w-16 h-16 rounded-full object-cover border-2 border-primary"
            />
          ) : student ? (
            <div className="w-16 h-16 rounded-full bg-gradient-accent flex items-center justify-center">
              <UserCheck className="w-8 h-8 text-white" />
            </div>
          ) : null}
          <div>
            <h1 className="text-3xl font-bold">{student?.name || 'تتبع الطالب'}</h1>
            <p className="text-muted-foreground mt-2">متابعة النشاط والموقع</p>
          </div>
        </div>
        <div className="w-64">
          <Label>اختر الطالب</Label>
          <Select
            value={selectedStudentId?.toString() || ''}
            onValueChange={(value) => {
              setSelectedStudentId(parseInt(value));
              navigate(`/admin/students/${value}/tracking`);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="اختر طالب" />
            </SelectTrigger>
            <SelectContent>
              {students?.map((s: any) => (
                <SelectItem key={s.id} value={s.id.toString()}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {trackingLoading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">جاري التحميل...</p>
        </div>
      ) : !student ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">الطالب غير موجود</p>
        </div>
      ) : (
        <>
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
                  {bus ? (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">رقم الحافلة</p>
                          <p className="font-semibold">{bus.bus_number}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">اسم السائق</p>
                          <p className="font-semibold">{bus.driver_name}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">رقم هاتف السائق</p>
                          <p className="font-semibold">{bus.driver_phone}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">حالة التتبع</p>
                          <Badge variant={trackingData?.tracker_active ? 'default' : 'secondary'}>
                            {trackingData?.tracker_active ? 'نشط' : 'غير نشط'}
                          </Badge>
                        </div>
                      </div>

                      {trackingData?.is_active_time && (
                        <div className="mt-4">
                          <Badge variant="default" className="mb-2">
                            التتبع اللحظي مفعل
                          </Badge>
                        </div>
                      )}
                      {!trackingData?.is_active_time && (
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
                        {lastAttendance.image_url && (
                          <div className="col-span-2">
                            <p className="text-sm text-muted-foreground mb-2">صورة الحضور</p>
                            <div className="border rounded-lg overflow-hidden">
                              <img
                                src={lastAttendance.image_url}
                                alt="Attendance image"
                                className="w-full h-auto max-h-96 object-contain"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = 'none';
                                }}
                              />
                            </div>
                          </div>
                        )}
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
                  <div className="mb-4 space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>من تاريخ</Label>
                        <Input
                          type="date"
                          value={filters.start_date}
                          onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>إلى تاريخ</Label>
                        <Input
                          type="date"
                          value={filters.end_date}
                          onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>الباص</Label>
                        <Input
                          type="number"
                          placeholder="رقم الباص"
                          value={filters.bus_id}
                          onChange={(e) => setFilters({ ...filters, bus_id: e.target.value })}
                        />
                      </div>
                    </div>
                    <Button onClick={handleFilterChange} className="w-full">
                      <Filter className="w-4 h-4 mr-2" />
                      تطبيق الفلاتر
                    </Button>
                  </div>

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
                            <div className="flex items-center gap-2">
                              {attendance.gps_latitude && attendance.gps_longitude && (
                                <Badge variant="outline">
                                  <MapPin className="w-3 h-3 mr-1" />
                                  موقع متاح
                                </Badge>
                              )}
                              {attendance.image_url && (
                                <Badge variant="outline">
                                  <ImageIcon className="w-3 h-3 mr-1" />
                                  صورة متاحة
                                </Badge>
                              )}
                            </div>
                          </div>
                          {attendance.image_url && (
                            <div className="mt-4">
                              <img
                                src={attendance.image_url}
                                alt="Attendance image"
                                className="w-full h-auto max-h-48 object-contain rounded-lg border"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = 'none';
                                }}
                              />
                            </div>
                          )}
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
        </>
      )}
    </div>
  );
};

export default AdminStudentTracking;