import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { getMyStudents } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { GraduationCap, MapPin, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { ar } from 'date-fns/locale';

const ParentDashboard: React.FC = () => {
  const { isParent } = useAuth();
  const navigate = useNavigate();

  const { data: students, isLoading } = useQuery({
    queryKey: ['my-students'],
    queryFn: getMyStudents,
    enabled: isParent,
  });

  if (!isParent) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">ليس لديك صلاحية للوصول إلى هذه الصفحة</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-slide-up">
      <div>
        <h1 className="text-3xl font-bold">لوحة تحكم ولي الأمر</h1>
        <p className="text-muted-foreground mt-2">متابعة أطفالك</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">جاري التحميل...</p>
        </div>
      ) : students?.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-muted-foreground">لا يوجد لديك أطفال مسجلين</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {students?.map((student: any) => (
            <Card key={student.id} className="glass-effect hover:shadow-elevated transition-all cursor-pointer">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-accent flex items-center justify-center">
                    <GraduationCap className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <CardTitle>{student.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {student.age} سنة - {student.gender === 'male' ? 'ذكر' : 'أنثى'}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {student.bus && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin className="w-4 h-4 text-muted-foreground" />
                      <span>الحافلة: {student.bus.bus_number}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-muted-foreground">السائق: {student.bus.driver_name}</span>
                    </div>
                  </div>
                )}
                <Button
                  className="w-full bg-gradient-accent"
                  onClick={() => navigate(`/parent/students/${student.id}`)}
                >
                  عرض التفاصيل
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ParentDashboard;

