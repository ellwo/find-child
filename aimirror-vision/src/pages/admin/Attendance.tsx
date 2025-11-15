import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAttendanceReport, getStudents, getBuses } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Filter, Image as ImageIcon, MapPin, UserCheck, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import { ar } from 'date-fns/locale';

const AdminAttendance: React.FC = () => {
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    bus_id: '',
    student_id: '',
  });
  const [skip, setSkip] = useState(0);
  const limit = 50;

  // Get students and buses for filters
  const { data: students } = useQuery({
    queryKey: ['all-students'],
    queryFn: () => getStudents(),
  });

  const { data: buses } = useQuery({
    queryKey: ['all-buses'],
    queryFn: () => getBuses(),
  });

  // Get attendance report
  const { data: attendanceData, refetch, isLoading } = useQuery({
    queryKey: ['attendance-report', filters, skip],
    queryFn: () => getAttendanceReport({
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
      bus_id: filters.bus_id ? parseInt(filters.bus_id) : undefined,
      student_id: filters.student_id ? parseInt(filters.student_id) : undefined,
      skip,
      limit,
    }),
  });

  const handleFilterChange = () => {
    setSkip(0);
    refetch();
  };

  const handleResetFilters = () => {
    setFilters({
      start_date: '',
      end_date: '',
      bus_id: '',
      student_id: '',
    });
    setSkip(0);
  };

  const attendances = attendanceData?.items || [];
  const total = attendanceData?.total || 0;
  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(skip / limit) + 1;

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-3xl font-bold">سجل الحضور</h1>
        <p className="text-muted-foreground mt-2">عرض وإدارة سجلات الحضور مع إمكانية الفلترة</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            فلاتر البحث
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
              <Select
                value={filters.bus_id || 'none'}
                onValueChange={(value) => setFilters({ ...filters, bus_id: value === 'none' ? '' : value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="اختر الباص" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">جميع الباصات</SelectItem>
                  {buses?.map((bus: any) => (
                    <SelectItem key={bus.id} value={bus.id.toString()}>
                      {bus.bus_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>الطالب</Label>
              <Select
                value={filters.student_id || 'none'}
                onValueChange={(value) => setFilters({ ...filters, student_id: value === 'none' ? '' : value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="اختر الطالب" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">جميع الطلاب</SelectItem>
                  {students?.map((student: any) => (
                    <SelectItem key={student.id} value={student.id.toString()}>
                      {student.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={handleFilterChange} className="flex-1">
              <Filter className="w-4 h-4 mr-2" />
              تطبيق الفلاتر
            </Button>
            <Button onClick={handleResetFilters} variant="outline">
              إعادة تعيين
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <UserCheck className="w-5 h-5" />
              سجلات الحضور
            </div>
            <Badge variant="secondary">
              إجمالي: {total} سجل
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">جاري التحميل...</p>
            </div>
          ) : attendances.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">لا توجد سجلات حضور</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الطالب</TableHead>
                      <TableHead>الباص</TableHead>
                      <TableHead>التاريخ والوقت</TableHead>
                      <TableHead>نسبة التطابق</TableHead>
                      <TableHead>الموقع</TableHead>
                      <TableHead>الصورة</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {attendances.map((attendance: any) => (
                      <TableRow key={attendance.id}>
                        <TableCell>
                          <div>
                            <p className="font-semibold">{attendance.student?.name || 'غير معروف'}</p>
                            <p className="text-sm text-muted-foreground">
                              {attendance.student?.age ? `العمر: ${attendance.student.age}` : ''}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          {attendance.bus?.bus_number || 'غير معروف'}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-muted-foreground" />
                            <div>
                              <p className="font-medium">
                                {format(new Date(attendance.detected_at), 'yyyy-MM-dd', { locale: ar })}
                              </p>
                              <p className="text-sm text-muted-foreground">
                                {format(new Date(attendance.detected_at), 'HH:mm:ss', { locale: ar })}
                              </p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={attendance.similarity_score >= 0.9 ? 'default' : 'secondary'}>
                            {(attendance.similarity_score * 100).toFixed(1)}%
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {attendance.gps_latitude && attendance.gps_longitude ? (
                            <Badge variant="outline" className="gap-1">
                              <MapPin className="w-3 h-3" />
                              متاح
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">غير متاح</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {attendance.image_url ? (
                            <div className="relative group">
                              <img
                                src={attendance.image_url}
                                alt="Attendance"
                                className="w-16 h-16 object-cover rounded-lg border cursor-pointer hover:scale-110 transition-transform"
                                onClick={() => window.open(attendance.image_url, '_blank')}
                              />
                              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                                <ImageIcon className="w-4 h-4 text-white" />
                              </div>
                            </div>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    الصفحة {currentPage} من {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setSkip(Math.max(0, skip - limit))}
                      disabled={skip === 0}
                    >
                      السابق
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setSkip(skip + limit)}
                      disabled={skip + limit >= total}
                    >
                      التالي
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminAttendance;

