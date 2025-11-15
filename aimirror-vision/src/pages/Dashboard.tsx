import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Bus, Users, GraduationCap, MapPin, LogIn, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const { isAuthenticated, isAdmin, isParent } = useAuth();

  // Show different content based on authentication status
  if (!isAuthenticated) {
    return (
      <div className="space-y-8 animate-slide-up">
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-primary bg-clip-text text-transparent">
            نظام تتبع الأطفال الأبوي
          </h1>
          <p className="text-muted-foreground text-lg">
            نظام متكامل لتتبع حافلات المدرسة والطلاب
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
          <Card className="glass-effect hover:shadow-elevated transition-all duration-300 hover:-translate-y-1">
            <CardHeader>
              <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center mb-4">
                <User className="w-6 h-6 text-white" />
              </div>
              <CardTitle>تسجيل دخول الإدارة</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">
                للوصول إلى لوحة التحكم وإدارة النظام
              </p>
              <Link to="/admin/login">
                <Button className="w-full bg-gradient-primary">
                  <LogIn className="w-4 h-4 mr-2" />
                  تسجيل الدخول
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="glass-effect hover:shadow-elevated transition-all duration-300 hover:-translate-y-1">
            <CardHeader>
              <div className="w-12 h-12 rounded-xl bg-gradient-accent flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-white" />
              </div>
              <CardTitle>تسجيل دخول ولي الأمر</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">
                لمتابعة أطفالك والتتبع اللحظي
              </p>
              <Link to="/parent/login">
                <Button className="w-full bg-gradient-accent">
                  <LogIn className="w-4 h-4 mr-2" />
                  تسجيل الدخول
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        <Card className="glass-effect shadow-card max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl">مميزات النظام</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <Bus className="w-12 h-12 mx-auto mb-4 text-primary" />
                <h3 className="font-bold mb-2">تتبع الحافلات</h3>
                <p className="text-sm text-muted-foreground">
                  تتبع لحظي لموقع الحافلات على الخريطة
                </p>
              </div>
              <div className="text-center">
                <GraduationCap className="w-12 h-12 mx-auto mb-4 text-primary" />
                <h3 className="font-bold mb-2">تسجيل الحضور</h3>
                <p className="text-sm text-muted-foreground">
                  تسجيل تلقائي للحضور باستخدام التعرف على الوجه
                </p>
              </div>
              <div className="text-center">
                <MapPin className="w-12 h-12 mx-auto mb-4 text-primary" />
                <h3 className="font-bold mb-2">متابعة الطلاب</h3>
                <p className="text-sm text-muted-foreground">
                  متابعة أطفالك ومعرفة آخر موقع للحافلة
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Redirect authenticated users to their dashboard
  if (isAdmin) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground mb-4">جاري التوجيه إلى لوحة التحكم...</p>
        <Link to="/admin/dashboard">
          <Button>الذهاب إلى لوحة التحكم</Button>
        </Link>
      </div>
    );
  }

  if (isParent) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground mb-4">جاري التوجيه إلى لوحة التحكم...</p>
        <Link to="/parent/dashboard">
          <Button>الذهاب إلى لوحة التحكم</Button>
        </Link>
      </div>
    );
  }

  return null;
};

export default Dashboard;
