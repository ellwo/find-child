import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { getDashboardStats } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Bus, Users, GraduationCap, UserCheck, Activity, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';

const AdminDashboard: React.FC = () => {
  const { isAdmin } = useAuth();

  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-dashboard-stats'],
    queryFn: getDashboardStats,
    enabled: isAdmin,
  });

  const statCards = [
    {
      title: 'إجمالي الحافلات',
      value: stats?.total_buses || 0,
      icon: Bus,
      gradient: 'bg-gradient-primary',
      link: '/admin/buses',
    },
    {
      title: 'الحافلات النشطة',
      value: stats?.active_buses || 0,
      icon: Activity,
      gradient: 'bg-gradient-accent',
      link: '/admin/buses',
    },
    {
      title: 'إجمالي الطلاب',
      value: stats?.total_students || 0,
      icon: GraduationCap,
      gradient: 'bg-gradient-primary',
      link: '/admin/students',
    },
    {
      title: 'إجمالي أولياء الأمور',
      value: stats?.total_parents || 0,
      icon: Users,
      gradient: 'bg-gradient-accent',
      link: '/admin/parents',
    },
    {
      title: 'حضور اليوم',
      value: stats?.total_attendances_today || 0,
      icon: UserCheck,
      gradient: 'bg-gradient-primary',
      link: '/admin/students',
    },
    {
      title: 'حافلات بتتبع نشط',
      value: stats?.buses_with_active_tracking || 0,
      icon: MapPin,
      gradient: 'bg-gradient-accent',
      link: '/admin/live-tracking',
    },
  ];

  if (!isAdmin) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">ليس لديك صلاحية للوصول إلى هذه الصفحة</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-slide-up">
      <div>
        <h1 className="text-3xl font-bold">لوحة التحكم - الإدارة</h1>
        <p className="text-muted-foreground mt-2">نظرة عامة على النظام</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Link key={index} to={stat.link}>
              <Card className="glass-effect hover:shadow-elevated transition-all duration-300 hover:-translate-y-1 cursor-pointer group">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.title}
                  </CardTitle>
                  <div
                    className={`w-12 h-12 rounded-xl ${stat.gradient} flex items-center justify-center group-hover:scale-110 transition-transform`}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">
                    {isLoading ? '...' : stat.value}
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default AdminDashboard;

