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
      <div className="space-y-6 sm:space-y-8 lg:space-y-10 animate-slide-up">
        {/* Hero Section */}
        <div className="text-center space-y-3 sm:space-y-4 px-2">
          <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 rounded-2xl sm:rounded-3xl bg-gradient-primary mx-auto mb-4 sm:mb-6 glow-effect">
            <Bus className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold bg-gradient-primary bg-clip-text text-transparent leading-tight">
            نظام رحلة آمنة
          </h1>
          <p className="text-sm sm:text-base md:text-lg lg:text-xl text-muted-foreground max-w-2xl mx-auto px-4">
            نظام متكامل لتتبع حافلات المدرسة والطلاب مع التعرف على الوجوه وتسجيل الحضور التلقائي
          </p>
        </div>

        {/* Login Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 lg:gap-8 max-w-4xl mx-auto px-2">
          <Card className="glass-effect hover:shadow-elevated transition-all duration-300 hover:-translate-y-1 border-2 hover:border-primary/20">
            <CardHeader className="pb-3 sm:pb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-primary flex items-center justify-center mb-3 sm:mb-4 mx-auto sm:mx-0">
                <User className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <CardTitle className="text-base sm:text-lg lg:text-xl text-center sm:text-right">تسجيل دخول الإدارة</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 sm:space-y-4">
              <p className="text-xs sm:text-sm text-muted-foreground text-center sm:text-right">
                للوصول إلى لوحة التحكم وإدارة النظام
              </p>
              <Link to="/admin/login" className="block">
                <Button className="w-full bg-gradient-primary text-sm sm:text-base">
                  <LogIn className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
                  تسجيل الدخول
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="glass-effect hover:shadow-elevated transition-all duration-300 hover:-translate-y-1 border-2 hover:border-primary/20">
            <CardHeader className="pb-3 sm:pb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-accent flex items-center justify-center mb-3 sm:mb-4 mx-auto sm:mx-0">
                <Users className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <CardTitle className="text-base sm:text-lg lg:text-xl text-center sm:text-right">تسجيل دخول ولي الأمر</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 sm:space-y-4">
              <p className="text-xs sm:text-sm text-muted-foreground text-center sm:text-right">
                لمتابعة أطفالك والتتبع اللحظي
              </p>
              <Link to="/parent/login" className="block">
                <Button className="w-full bg-gradient-accent text-sm sm:text-base">
                  <LogIn className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
                  تسجيل الدخول
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Features Section */}
        <Card className="glass-effect shadow-card max-w-6xl mx-auto border-2">
          <CardHeader className="pb-3 sm:pb-4">
            <CardTitle className="text-xl sm:text-2xl lg:text-3xl text-center">مميزات النظام</CardTitle>
          </CardHeader>
          <CardContent className="pt-2 sm:pt-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
              <div className="text-center p-4 sm:p-6 rounded-xl hover:bg-muted/50 transition-colors">
                <div className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-3 sm:mb-4">
                  <Bus className="w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10 text-primary" />
                </div>
                <h3 className="font-bold text-sm sm:text-base lg:text-lg mb-2">تتبع الحافلات</h3>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  تتبع لحظي لموقع الحافلات على الخريطة مع تحديثات فورية
                </p>
              </div>
              <div className="text-center p-4 sm:p-6 rounded-xl hover:bg-muted/50 transition-colors">
                <div className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-3 sm:mb-4">
                  <GraduationCap className="w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10 text-primary" />
                </div>
                <h3 className="font-bold text-sm sm:text-base lg:text-lg mb-2">تسجيل الحضور</h3>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  تسجيل تلقائي للحضور باستخدام التعرف على الوجه بالذكاء الاصطناعي
                </p>
              </div>
              <div className="text-center p-4 sm:p-6 rounded-xl hover:bg-muted/50 transition-colors sm:col-span-2 lg:col-span-1">
                <div className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-3 sm:mb-4">
                  <MapPin className="w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10 text-primary" />
                </div>
                <h3 className="font-bold text-sm sm:text-base lg:text-lg mb-2">متابعة الطلاب</h3>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  متابعة أطفالك ومعرفة آخر موقع للحافلة في الوقت الفعلي
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
      <div className="text-center py-8 sm:py-12 px-4">
        <p className="text-muted-foreground mb-4 text-sm sm:text-base">جاري التوجيه إلى لوحة التحكم...</p>
        <Link to="/admin/dashboard">
          <Button className="text-sm sm:text-base">الذهاب إلى لوحة التحكم</Button>
        </Link>
      </div>
    );
  }

  if (isParent) {
    return (
      <div className="text-center py-8 sm:py-12 px-4">
        <p className="text-muted-foreground mb-4 text-sm sm:text-base">جاري التوجيه إلى لوحة التحكم...</p>
        <Link to="/parent/dashboard">
          <Button className="text-sm sm:text-base">الذهاب إلى لوحة التحكم</Button>
        </Link>
      </div>
    );
  }

  return null;
};

export default Dashboard;
