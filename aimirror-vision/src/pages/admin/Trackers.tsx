import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTrackers, createTracker, updateTracker } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { MapPin, Plus, Edit, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { format } from 'date-fns';
import { ar } from 'date-fns/locale';
import { Badge } from '@/components/ui/badge';

const AdminTrackers: React.FC = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingTracker, setEditingTracker] = useState<any>(null);
  const [formData, setFormData] = useState({
    device_id: '',
    device_name: '',
    is_active: true,
  });

  const queryClient = useQueryClient();

  const { data: trackers, isLoading } = useQuery({
    queryKey: ['trackers'],
    queryFn: getTrackers,
  });

  const createMutation = useMutation({
    mutationFn: createTracker,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trackers'] });
      toast({ title: 'تم إضافة جهاز التتبع بنجاح' });
      setIsDialogOpen(false);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في إضافة جهاز التتبع',
        variant: 'destructive',
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateTracker(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trackers'] });
      toast({ title: 'تم تحديث جهاز التتبع بنجاح' });
      setIsDialogOpen(false);
      setEditingTracker(null);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في تحديث جهاز التتبع',
        variant: 'destructive',
      });
    },
  });

  const resetForm = () => {
    setFormData({
      device_id: '',
      device_name: '',
      is_active: true,
    });
  };

  const handleEdit = (tracker: any) => {
    setEditingTracker(tracker);
    setFormData({
      device_id: tracker.device_id,
      device_name: tracker.device_name || '',
      is_active: tracker.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      device_id: formData.device_id.trim(),
      device_name: formData.device_name.trim() || null,
      is_active: formData.is_active,
    };

    if (editingTracker) {
      updateMutation.mutate({ id: editingTracker.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'غير متاح';
    try {
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm:ss', { locale: ar });
    } catch {
      return 'غير متاح';
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">إدارة أجهزة التتبع GPS</h1>
          <p className="text-muted-foreground mt-2">إدارة أجهزة GPS للحافلات</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingTracker(null); resetForm(); }}>
              <Plus className="w-4 h-4 mr-2" />
              إضافة جهاز تتبع
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>{editingTracker ? 'تعديل جهاز التتبع' : 'إضافة جهاز تتبع جديد'}</DialogTitle>
              <DialogDescription>
                {editingTracker ? 'قم بتعديل معلومات جهاز التتبع' : 'أدخل معلومات جهاز التتبع الجديد'}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>معرف الجهاز (Device ID) *</Label>
                <Input
                  value={formData.device_id}
                  onChange={(e) => setFormData({ ...formData, device_id: e.target.value })}
                  placeholder="مثال: GPS_TRACKER_001"
                  required
                  disabled={!!editingTracker} // Cannot change device_id after creation
                />
                {editingTracker && (
                  <p className="text-xs text-muted-foreground mt-1">
                    لا يمكن تغيير معرف الجهاز بعد الإنشاء
                  </p>
                )}
              </div>
              <div>
                <Label>اسم الجهاز (اختياري)</Label>
                <Input
                  value={formData.device_name}
                  onChange={(e) => setFormData({ ...formData, device_name: e.target.value })}
                  placeholder="مثال: Bus 1 GPS Tracker"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="is_active">حالة الجهاز</Label>
                <Switch
                  id="is_active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsDialogOpen(false);
                    setEditingTracker(null);
                    resetForm();
                  }}
                >
                  إلغاء
                </Button>
                <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                  {(createMutation.isPending || updateMutation.isPending) && (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  )}
                  {editingTracker ? 'تحديث' : 'إضافة'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>قائمة أجهزة التتبع</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : !trackers || trackers.length === 0 ? (
            <div className="text-center py-12">
              <MapPin className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">لا توجد أجهزة تتبع</p>
              <Button
                className="mt-4"
                onClick={() => {
                  setEditingTracker(null);
                  resetForm();
                  setIsDialogOpen(true);
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                إضافة جهاز تتبع
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>معرف الجهاز</TableHead>
                    <TableHead>اسم الجهاز</TableHead>
                    <TableHead>الحالة</TableHead>
                    <TableHead>آخر موقع</TableHead>
                    <TableHead>آخر تحديث</TableHead>
                    <TableHead className="text-right">الإجراءات</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trackers.map((tracker: any) => (
                    <TableRow key={tracker.id}>
                      <TableCell className="font-mono font-semibold">
                        {tracker.device_id}
                      </TableCell>
                      <TableCell>
                        {tracker.device_name || (
                          <span className="text-muted-foreground">بدون اسم</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {tracker.is_active ? (
                          <Badge variant="default" className="bg-green-500">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            نشط
                          </Badge>
                        ) : (
                          <Badge variant="secondary">
                            <XCircle className="w-3 h-3 mr-1" />
                            غير نشط
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {tracker.last_latitude && tracker.last_longitude ? (
                          <div className="text-sm">
                            <div className="font-mono">
                              {tracker.last_latitude.toFixed(6)}, {tracker.last_longitude.toFixed(6)}
                            </div>
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-sm">لا يوجد موقع</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {tracker.last_update_timestamp ? (
                          <div className="text-sm">
                            {formatDate(tracker.last_update_timestamp)}
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-sm">لم يتم التحديث</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(tracker)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminTrackers;

