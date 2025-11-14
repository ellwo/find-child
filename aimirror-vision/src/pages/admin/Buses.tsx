import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBuses, createBus, updateBus, deleteBus, getTrackers, getCameras } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from '@/hooks/use-toast';
import { Bus as BusIcon, Plus, Edit, Trash2, Loader2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const AdminBuses: React.FC = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingBus, setEditingBus] = useState<any>(null);
  const [formData, setFormData] = useState({
    bus_number: '',
    driver_name: '',
    driver_phone: '',
    gps_tracker_id: '',
    camera_id: '',
    morning_start: '',
    morning_end: '',
    afternoon_start: '',
    afternoon_end: '',
    is_active: true,
  });

  const queryClient = useQueryClient();

  const { data: buses, isLoading } = useQuery({
    queryKey: ['buses'],
    queryFn: getBuses,
  });

  const { data: trackers } = useQuery({
    queryKey: ['trackers'],
    queryFn: getTrackers,
  });

  const { data: cameras } = useQuery({
    queryKey: ['cameras'],
    queryFn: getCameras,
  });

  const createMutation = useMutation({
    mutationFn: createBus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['buses'] });
      toast({ title: 'تم إضافة الحافلة بنجاح' });
      setIsDialogOpen(false);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في إضافة الحافلة',
        variant: 'destructive',
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateBus(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['buses'] });
      toast({ title: 'تم تحديث الحافلة بنجاح' });
      setIsDialogOpen(false);
      setEditingBus(null);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في تحديث الحافلة',
        variant: 'destructive',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteBus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['buses'] });
      toast({ title: 'تم حذف الحافلة بنجاح' });
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في حذف الحافلة',
        variant: 'destructive',
      });
    },
  });

  const resetForm = () => {
    setFormData({
      bus_number: '',
      driver_name: '',
      driver_phone: '',
      gps_tracker_id: '',
      camera_id: '',
      morning_start: '',
      morning_end: '',
      afternoon_start: '',
      afternoon_end: '',
      is_active: true,
    });
  };

  const handleEdit = (bus: any) => {
    setEditingBus(bus);
    setFormData({
      bus_number: bus.bus_number,
      driver_name: bus.driver_name,
      driver_phone: bus.driver_phone,
      gps_tracker_id: bus.gps_tracker_id?.toString() || '',
      camera_id: bus.camera_id || '',
      morning_start: bus.morning_start || '',
      morning_end: bus.morning_end || '',
      afternoon_start: bus.afternoon_start || '',
      afternoon_end: bus.afternoon_end || '',
      is_active: bus.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ...formData,
      gps_tracker_id: formData.gps_tracker_id ? parseInt(formData.gps_tracker_id) : null,
      camera_id: formData.camera_id || null,
    };

    if (editingBus) {
      updateMutation.mutate({ id: editingBus.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">إدارة الحافلات</h1>
          <p className="text-muted-foreground mt-2">إدارة حافلات المدرسة</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingBus(null); resetForm(); }}>
              <Plus className="w-4 h-4 mr-2" />
              إضافة حافلة
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingBus ? 'تعديل حافلة' : 'إضافة حافلة جديدة'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>رقم الحافلة</Label>
                  <Input
                    value={formData.bus_number}
                    onChange={(e) => setFormData({ ...formData, bus_number: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>اسم السائق</Label>
                  <Input
                    value={formData.driver_name}
                    onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>رقم هاتف السائق</Label>
                  <Input
                    value={formData.driver_phone}
                    onChange={(e) => setFormData({ ...formData, driver_phone: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>جهاز التتبع GPS</Label>
                  <Select
                    value={formData.gps_tracker_id}
                    onValueChange={(value) => setFormData({ ...formData, gps_tracker_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="اختر جهاز التتبع" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">لا يوجد</SelectItem>
                      {trackers?.map((tracker: any) => (
                        <SelectItem key={tracker.id} value={tracker.id.toString()}>
                          {tracker.device_id} - {tracker.device_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>الكاميرا</Label>
                  <Select
                    value={formData.camera_id}
                    onValueChange={(value) => setFormData({ ...formData, camera_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="اختر الكاميرا" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">لا يوجد</SelectItem>
                      {cameras?.map((camera: any) => (
                        <SelectItem key={camera.code} value={camera.code}>
                          {camera.code} - {camera.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>وقت بداية الذهاب (HH:MM)</Label>
                  <Input
                    type="time"
                    value={formData.morning_start}
                    onChange={(e) => setFormData({ ...formData, morning_start: e.target.value })}
                  />
                </div>
                <div>
                  <Label>وقت نهاية الذهاب (HH:MM)</Label>
                  <Input
                    type="time"
                    value={formData.morning_end}
                    onChange={(e) => setFormData({ ...formData, morning_end: e.target.value })}
                  />
                </div>
                <div>
                  <Label>وقت بداية العودة (HH:MM)</Label>
                  <Input
                    type="time"
                    value={formData.afternoon_start}
                    onChange={(e) => setFormData({ ...formData, afternoon_start: e.target.value })}
                  />
                </div>
                <div>
                  <Label>وقت نهاية العودة (HH:MM)</Label>
                  <Input
                    type="time"
                    value={formData.afternoon_end}
                    onChange={(e) => setFormData({ ...formData, afternoon_end: e.target.value })}
                  />
                </div>
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending || updateMutation.isPending}>
                {(createMutation.isPending || updateMutation.isPending) ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : null}
                {editingBus ? 'تحديث' : 'إضافة'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>قائمة الحافلات</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <Loader2 className="w-8 h-8 animate-spin mx-auto" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>رقم الحافلة</TableHead>
                  <TableHead>اسم السائق</TableHead>
                  <TableHead>رقم الهاتف</TableHead>
                  <TableHead>جهاز التتبع</TableHead>
                  <TableHead>الكاميرا</TableHead>
                  <TableHead>الحالة</TableHead>
                  <TableHead>الإجراءات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {buses?.map((bus: any) => (
                  <TableRow key={bus.id}>
                    <TableCell>{bus.bus_number}</TableCell>
                    <TableCell>{bus.driver_name}</TableCell>
                    <TableCell>{bus.driver_phone}</TableCell>
                    <TableCell>{bus.gps_tracker?.device_id || '-'}</TableCell>
                    <TableCell>{bus.camera_id || '-'}</TableCell>
                    <TableCell>
                      <span className={bus.is_active ? 'text-green-600' : 'text-red-600'}>
                        {bus.is_active ? 'نشط' : 'غير نشط'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => handleEdit(bus)}>
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => {
                            if (confirm('هل أنت متأكد من حذف هذه الحافلة؟')) {
                              deleteMutation.mutate(bus.id);
                            }
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminBuses;

