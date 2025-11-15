import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getStudents, createStudent, updateStudent, deleteStudent, getBuses, getParents } from '@/lib/api';
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
import { GraduationCap, Plus, Edit, Trash2, Loader2, Upload, MapPin } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import GoogleMapComponent from '@/components/GoogleMap';

const AdminStudents: React.FC = () => {
  const navigate = useNavigate();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<any>(null);
  const [faceImage, setFaceImage] = useState<File | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: 'male',
    parent_id: '',
    bus_id: 'none',
    home_address: '',
    home_latitude: '',
    home_longitude: '',
  });
  const [mapCenter, setMapCenter] = useState({ lat: 24.7136, lng: 46.6753 }); // Default to Riyadh

  const queryClient = useQueryClient();

  const { data: students, isLoading } = useQuery({
    queryKey: ['students'],
    queryFn: getStudents,
  });

  const { data: buses } = useQuery({
    queryKey: ['buses'],
    queryFn: getBuses,
  });

  const { data: parents } = useQuery({
    queryKey: ['parents'],
    queryFn: getParents,
  });

  const createMutation = useMutation({
    mutationFn: (data: { studentData: any; faceImage?: File }) => createStudent(data.studentData, data.faceImage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      toast({ title: 'تم إضافة الطالب بنجاح' });
      setIsDialogOpen(false);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في إضافة الطالب',
        variant: 'destructive',
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { studentData: any; faceImage?: File } }) =>
      updateStudent(id, data.studentData, data.faceImage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      toast({ title: 'تم تحديث الطالب بنجاح' });
      setIsDialogOpen(false);
      setEditingStudent(null);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في تحديث الطالب',
        variant: 'destructive',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteStudent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      toast({ title: 'تم حذف الطالب بنجاح' });
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في حذف الطالب',
        variant: 'destructive',
      });
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      age: '',
      gender: 'male',
      parent_id: '',
      bus_id: 'none',
      home_address: '',
      home_latitude: '',
      home_longitude: '',
    });
    setFaceImage(null);
  };

  const handleEdit = (student: any) => {
    setEditingStudent(student);
    setFormData({
      name: student.name,
      age: student.age.toString(),
      gender: student.gender,
      parent_id: student.parent_id?.toString() || '',
      bus_id: student.bus_id?.toString() || 'none',
      home_address: student.home_address || '',
      home_latitude: student.home_latitude?.toString() || '',
      home_longitude: student.home_longitude?.toString() || '',
    });
    if (student.home_latitude && student.home_longitude) {
      setMapCenter({ lat: student.home_latitude, lng: student.home_longitude });
    }
    setIsDialogOpen(true);
  };

  const handleMapClick = (e: any) => {
    const lat = e.latLng.lat();
    const lng = e.latLng.lng();
    setFormData({
      ...formData,
      home_latitude: lat.toString(),
      home_longitude: lng.toString(),
    });
    setMapCenter({ lat, lng });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.parent_id) {
      toast({
        title: 'خطأ',
        description: 'يجب اختيار ولي الأمر',
        variant: 'destructive',
      });
      return;
    }
    
    const studentData: any = {
      name: formData.name,
      age: parseInt(formData.age),
      gender: formData.gender,
      parent_id: parseInt(formData.parent_id),
      bus_id: formData.bus_id && formData.bus_id !== 'none' ? parseInt(formData.bus_id) : null,
      home_address: formData.home_address || null,
      home_latitude: formData.home_latitude ? parseFloat(formData.home_latitude) : null,
      home_longitude: formData.home_longitude ? parseFloat(formData.home_longitude) : null,
    };

    if (editingStudent) {
      updateMutation.mutate({ id: editingStudent.id, data: { studentData, faceImage: faceImage || undefined } });
    } else {
      createMutation.mutate({ studentData, faceImage: faceImage || undefined });
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">إدارة الطلاب</h1>
          <p className="text-muted-foreground mt-2">إدارة بيانات الطلاب</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingStudent(null); resetForm(); }}>
              <Plus className="w-4 h-4 mr-2" />
              إضافة طالب
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingStudent ? 'تعديل طالب' : 'إضافة طالب جديد'}</DialogTitle>
              <DialogDescription>
                {editingStudent ? 'قم بتعديل معلومات الطالب' : 'أدخل معلومات الطالب الجديد'}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>اسم الطالب</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>العمر</Label>
                  <Input
                    type="number"
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>النوع</Label>
                  <Select
                    value={formData.gender}
                    onValueChange={(value) => setFormData({ ...formData, gender: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">ذكر</SelectItem>
                      <SelectItem value="female">أنثى</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>ولي الأمر *</Label>
                  <Select
                    value={formData.parent_id || undefined}
                    onValueChange={(value) => setFormData({ ...formData, parent_id: value })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="اختر ولي الأمر" />
                    </SelectTrigger>
                    <SelectContent>
                      {parents?.map((parent: any) => (
                        <SelectItem key={parent.id} value={parent.id.toString()}>
                          {parent.username}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>الحافلة</Label>
                  <Select
                    value={formData.bus_id || 'none'}
                    onValueChange={(value) => setFormData({ ...formData, bus_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="اختر الحافلة" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">لا يوجد</SelectItem>
                      {buses?.map((bus: any) => (
                        <SelectItem key={bus.id} value={bus.id.toString()}>
                          {bus.bus_number}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>صورة الوجه</Label>
                  <Input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setFaceImage(e.target.files?.[0] || null)}
                  />
                </div>
              </div>
              <div>
                <Label>عنوان المنزل</Label>
                <Input
                  value={formData.home_address}
                  onChange={(e) => setFormData({ ...formData, home_address: e.target.value })}
                />
              </div>
              <div>
                <Label>موقع المنزل على الخريطة (انقر على الخريطة لتحديد الموقع)</Label>
                <div className="border rounded-lg overflow-hidden">
                  <GoogleMapComponent
                    center={mapCenter}
                    zoom={15}
                    markers={
                      formData.home_latitude && formData.home_longitude
                        ? [
                            {
                              lat: parseFloat(formData.home_latitude),
                              lng: parseFloat(formData.home_longitude),
                              label: 'المنزل',
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
                      value={formData.home_latitude}
                      onChange={(e) => {
                        const lat = parseFloat(e.target.value);
                        if (!isNaN(lat)) {
                          setFormData({ ...formData, home_latitude: e.target.value });
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
                      value={formData.home_longitude}
                      onChange={(e) => {
                        const lng = parseFloat(e.target.value);
                        if (!isNaN(lng)) {
                          setFormData({ ...formData, home_longitude: e.target.value });
                          setMapCenter({ lat: mapCenter.lat, lng });
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending || updateMutation.isPending}>
                {(createMutation.isPending || updateMutation.isPending) ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : null}
                {editingStudent ? 'تحديث' : 'إضافة'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>قائمة الطلاب</CardTitle>
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
                  <TableHead>الصورة</TableHead>
                  <TableHead>الاسم</TableHead>
                  <TableHead>العمر</TableHead>
                  <TableHead>النوع</TableHead>
                  <TableHead>ولي الأمر</TableHead>
                  <TableHead>الحافلة</TableHead>
                  <TableHead>الإجراءات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {students?.map((student: any) => (
                  <TableRow key={student.id}>
                    <TableCell>
                      {student.image_url ? (
                        <img 
                          src={student.image_url} 
                          alt={student.name}
                          className="w-12 h-12 object-cover rounded-full border"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                          <GraduationCap className="w-6 h-6 text-muted-foreground" />
                        </div>
                      )}
                    </TableCell>
                    <TableCell>{student.name}</TableCell>
                    <TableCell>{student.age}</TableCell>
                    <TableCell>{student.gender === 'male' ? 'ذكر' : 'أنثى'}</TableCell>
                    <TableCell>{student.parent?.username || '-'}</TableCell>
                    <TableCell>{student.bus?.bus_number || '-'}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button 
                          size="sm" 
                          variant="default" 
                          onClick={() => navigate(`/admin/students/${student.id}/tracking`)}
                          title="تتبع الطالب"
                        >
                          <MapPin className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleEdit(student)} title="تعديل">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => {
                            if (confirm('هل أنت متأكد من حذف هذا الطالب؟')) {
                              deleteMutation.mutate(student.id);
                            }
                          }}
                          title="حذف"
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

export default AdminStudents;

