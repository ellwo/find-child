import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from '@/hooks/use-toast';
import { Settings as SettingsIcon, Loader2, Save } from 'lucide-react';
import GoogleMapComponent from '@/components/GoogleMap';

const AdminSettings: React.FC = () => {
  const [formData, setFormData] = useState({
    school_name: '',
    school_address: '',
    school_latitude: '',
    school_longitude: '',
    default_morning_start: '',
    default_morning_end: '',
    default_afternoon_start: '',
    default_afternoon_end: '',
    attendance_interval_minutes: '5',
    websocket_enabled: true,
  });
  const [mapCenter, setMapCenter] = useState({ lat: 24.7136, lng: 46.6753 });

  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
  });

  useEffect(() => {
    if (settings) {
      setFormData({
        school_name: settings.school_name || '',
        school_address: settings.school_address || '',
        school_latitude: settings.school_latitude?.toString() || '',
        school_longitude: settings.school_longitude?.toString() || '',
        default_morning_start: settings.default_morning_start || '',
        default_morning_end: settings.default_morning_end || '',
        default_afternoon_start: settings.default_afternoon_start || '',
        default_afternoon_end: settings.default_afternoon_end || '',
        attendance_interval_minutes: settings.attendance_interval_minutes?.toString() || '5',
        websocket_enabled: settings.websocket_enabled ?? true,
      });
      if (settings.school_latitude && settings.school_longitude) {
        setMapCenter({ lat: settings.school_latitude, lng: settings.school_longitude });
      }
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      toast({ title: 'تم حفظ الإعدادات بنجاح' });
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في حفظ الإعدادات',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      school_name: formData.school_name,
      school_address: formData.school_address || undefined,
      school_latitude: formData.school_latitude ? parseFloat(formData.school_latitude) : undefined,
      school_longitude: formData.school_longitude ? parseFloat(formData.school_longitude) : undefined,
      default_morning_start: formData.default_morning_start || undefined,
      default_morning_end: formData.default_morning_end || undefined,
      default_afternoon_start: formData.default_afternoon_start || undefined,
      default_afternoon_end: formData.default_afternoon_end || undefined,
      attendance_interval_minutes: parseInt(formData.attendance_interval_minutes),
      websocket_enabled: formData.websocket_enabled,
    };
    updateMutation.mutate(data);
  };

  const handleMapClick = (e: any) => {
    const lat = e.latLng.lat();
    const lng = e.latLng.lng();
    setFormData({
      ...formData,
      school_latitude: lat.toString(),
      school_longitude: lng.toString(),
    });
    setMapCenter({ lat, lng });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-3xl font-bold">إعدادات النظام</h1>
        <p className="text-muted-foreground mt-2">إدارة إعدادات النظام العامة</p>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <SettingsIcon className="w-5 h-5" />
              معلومات المدرسة
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>اسم المدرسة</Label>
              <Input
                value={formData.school_name}
                onChange={(e) => setFormData({ ...formData, school_name: e.target.value })}
                required
              />
            </div>
            <div>
              <Label>عنوان المدرسة</Label>
              <Input
                value={formData.school_address}
                onChange={(e) => setFormData({ ...formData, school_address: e.target.value })}
              />
            </div>
            <div>
              <Label>موقع المدرسة على الخريطة (انقر على الخريطة لتحديد الموقع)</Label>
              <div className="border rounded-lg overflow-hidden">
                <GoogleMapComponent
                  center={mapCenter}
                  zoom={15}
                  markers={
                    formData.school_latitude && formData.school_longitude
                      ? [
                          {
                            lat: parseFloat(formData.school_latitude),
                            lng: parseFloat(formData.school_longitude),
                            label: 'المدرسة',
                          },
                        ]
                      : []
                  }
                  onMapClick={handleMapClick}
                  height="300px"
                />
              </div>
              <div className="grid grid-cols-2 gap-4 mt-2">
                <div>
                  <Label>خط العرض</Label>
                  <Input
                    type="number"
                    step="any"
                    value={formData.school_latitude}
                    onChange={(e) => {
                      const lat = parseFloat(e.target.value);
                      if (!isNaN(lat)) {
                        setFormData({ ...formData, school_latitude: e.target.value });
                        setMapCenter({ lat, lng: mapCenter.lng });
                      }
                    }}
                  />
                </div>
                <div>
                  <Label>خط الطول</Label>
                  <Input
                    type="number"
                    step="any"
                    value={formData.school_longitude}
                    onChange={(e) => {
                      const lng = parseFloat(e.target.value);
                      if (!isNaN(lng)) {
                        setFormData({ ...formData, school_longitude: e.target.value });
                        setMapCenter({ lat: mapCenter.lat, lng });
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>أوقات النشاط الافتراضية</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>وقت بداية الذهاب (HH:MM)</Label>
                <Input
                  type="time"
                  value={formData.default_morning_start}
                  onChange={(e) => setFormData({ ...formData, default_morning_start: e.target.value })}
                />
              </div>
              <div>
                <Label>وقت نهاية الذهاب (HH:MM)</Label>
                <Input
                  type="time"
                  value={formData.default_morning_end}
                  onChange={(e) => setFormData({ ...formData, default_morning_end: e.target.value })}
                />
              </div>
              <div>
                <Label>وقت بداية العودة (HH:MM)</Label>
                <Input
                  type="time"
                  value={formData.default_afternoon_start}
                  onChange={(e) => setFormData({ ...formData, default_afternoon_start: e.target.value })}
                />
              </div>
              <div>
                <Label>وقت نهاية العودة (HH:MM)</Label>
                <Input
                  type="time"
                  value={formData.default_afternoon_end}
                  onChange={(e) => setFormData({ ...formData, default_afternoon_end: e.target.value })}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>إعدادات الحضور</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>فارق التحضير (بالدقائق)</Label>
              <Input
                type="number"
                value={formData.attendance_interval_minutes}
                onChange={(e) => setFormData({ ...formData, attendance_interval_minutes: e.target.value })}
                min="1"
                required
              />
              <p className="text-sm text-muted-foreground mt-1">
                الحد الأدنى للوقت بين تسجيلين متتاليين للحضور
              </p>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label>تفعيل WebSocket</Label>
                <p className="text-sm text-muted-foreground">تفعيل التحديثات اللحظية</p>
              </div>
              <Switch
                checked={formData.websocket_enabled}
                onCheckedChange={(checked) => setFormData({ ...formData, websocket_enabled: checked })}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" disabled={updateMutation.isPending}>
            {updateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                جاري الحفظ...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                حفظ الإعدادات
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default AdminSettings;

