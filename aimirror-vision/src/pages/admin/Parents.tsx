import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getParents, createParent, updateParent, deleteParent } from '@/lib/api';
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
import { Users, Plus, Edit, Trash2, Loader2 } from 'lucide-react';

const AdminParents: React.FC = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingParent, setEditingParent] = useState<any>(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone: '',
    password: '',
  });

  const queryClient = useQueryClient();

  const { data: parents, isLoading } = useQuery({
    queryKey: ['parents'],
    queryFn: getParents,
  });

  const createMutation = useMutation({
    mutationFn: createParent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents'] });
      toast({ title: 'تم إضافة ولي الأمر بنجاح' });
      setIsDialogOpen(false);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في إضافة ولي الأمر',
        variant: 'destructive',
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateParent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents'] });
      toast({ title: 'تم تحديث ولي الأمر بنجاح' });
      setIsDialogOpen(false);
      setEditingParent(null);
      resetForm();
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في تحديث ولي الأمر',
        variant: 'destructive',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteParent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parents'] });
      toast({ title: 'تم حذف ولي الأمر بنجاح' });
    },
    onError: (error: any) => {
      toast({
        title: 'خطأ',
        description: error.response?.data?.detail || 'فشل في حذف ولي الأمر',
        variant: 'destructive',
      });
    },
  });

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      phone: '',
      password: '',
    });
  };

  const handleEdit = (parent: any) => {
    setEditingParent(parent);
    setFormData({
      username: parent.username,
      email: parent.email || '',
      phone: parent.phone || '',
      password: '',
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: any = {
      username: formData.username,
      email: formData.email || undefined,
      phone: formData.phone || undefined,
    };
    if (formData.password) {
      data.password = formData.password;
    }

    if (editingParent) {
      updateMutation.mutate({ id: editingParent.id, data });
    } else {
      data.password = formData.password;
      createMutation.mutate(data);
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">إدارة أولياء الأمور</h1>
          <p className="text-muted-foreground mt-2">إدارة حسابات أولياء الأمور</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingParent(null); resetForm(); }}>
              <Plus className="w-4 h-4 mr-2" />
              إضافة ولي أمر
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingParent ? 'تعديل ولي أمر' : 'إضافة ولي أمر جديد'}</DialogTitle>
              <DialogDescription>
                {editingParent ? 'قم بتعديل معلومات ولي الأمر' : 'أدخل معلومات ولي الأمر الجديد'}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>اسم المستخدم</Label>
                <Input
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label>البريد الإلكتروني</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div>
                <Label>رقم الهاتف</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>
              <div>
                <Label>كلمة المرور {editingParent && '(اتركه فارغاً للاحتفاظ بالكلمة الحالية)'}</Label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required={!editingParent}
                />
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending || updateMutation.isPending}>
                {(createMutation.isPending || updateMutation.isPending) ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : null}
                {editingParent ? 'تحديث' : 'إضافة'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>قائمة أولياء الأمور</CardTitle>
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
                  <TableHead>اسم المستخدم</TableHead>
                  <TableHead>البريد الإلكتروني</TableHead>
                  <TableHead>رقم الهاتف</TableHead>
                  <TableHead>الحالة</TableHead>
                  <TableHead>الإجراءات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {parents?.map((parent: any) => (
                  <TableRow key={parent.id}>
                    <TableCell>{parent.username}</TableCell>
                    <TableCell>{parent.email || '-'}</TableCell>
                    <TableCell>{parent.phone || '-'}</TableCell>
                    <TableCell>
                      <span className={parent.is_active ? 'text-green-600' : 'text-red-600'}>
                        {parent.is_active ? 'نشط' : 'غير نشط'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => handleEdit(parent)}>
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => {
                            if (confirm('هل أنت متأكد من حذف ولي الأمر هذا؟')) {
                              deleteMutation.mutate(parent.id);
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

export default AdminParents;

