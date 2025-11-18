import React from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { getCameras, getSavedImages, getCurrentUser } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Camera, Images, Activity, TrendingUp, AlertCircle, Search, LogIn, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const token = localStorage.getItem('token');
  const isAuthenticated = !!token;

  // Only fetch admin data if authenticated
  const { data: cameras, isLoading: loadingCameras } = useQuery({
    queryKey: ['cameras'],
    queryFn: getCameras,
    enabled: isAuthenticated,
  });

  const { data: todayImages, isLoading: loadingImages } = useQuery({
    queryKey: ['today-images'],
    queryFn: () => getSavedImages({ page_size: 5 }),
    retry: false,
    enabled: isAuthenticated,
  });

  // Public options
  const publicOptions = [
    {
      title: t('dashboard.reportMissing'),
      description: t('dashboard.reportMissingDesc'),
      icon: AlertCircle,
      link: '/report',
      gradient: 'bg-gradient-primary',
    },
    {
      title: t('dashboard.trackReport'),
      description: t('dashboard.trackReportDesc'),
      icon: FileText,
      link: '/track',
      gradient: 'bg-gradient-accent',
    },
    {
      title: t('dashboard.search'),
      description: t('dashboard.searchDesc'),
      icon: Search,
      link: '/search',
      gradient: 'bg-gradient-primary',
    },
    {
      title: t('dashboard.login'),
      description: t('dashboard.loginDesc'),
      icon: LogIn,
      link: '/login',
      gradient: 'bg-gradient-accent',
    },
  ];

  // Admin stats (only if authenticated)
  const stats = isAuthenticated ? [
    {
      title: t('dashboard.totalCameras'),
      value: cameras?.length || 0,
      icon: Camera,
      gradient: 'bg-gradient-primary',
      link: '/cameras',
    },
    {
      title: t('dashboard.totalImages'),
      value: todayImages?.total || 0,
      icon: Images,
      gradient: 'bg-gradient-accent',
      link: '/saved-images',
    },
    {
      title: t('dashboard.activeCameras'),
      value: cameras?.filter((c: any) => c.last_seen)?.length || 0,
      icon: Activity,
      gradient: 'bg-gradient-primary',
      link: '/cameras',
    },
    {
      title: t('dashboard.todayImages'),
      value: todayImages?.items?.length || 0,
      icon: TrendingUp,
      gradient: 'bg-gradient-accent',
      link: '/saved-images',
    },
  ] : [];

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Welcome Section */}
      <div className="text-center space-y-2">
        <h1 className="text-4xl md:text-5xl font-bold bg-gradient-primary bg-clip-text text-transparent">
          {t('dashboard.welcome')}
        </h1>
        <p className="text-muted-foreground text-lg">
          {t('dashboard.title')}
        </p>
      </div>

      {/* Public Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {publicOptions.map((option, index) => {
          const Icon = option.icon;
          return (
            <Link key={index} to={option.link}>
              <Card className="glass-effect hover:shadow-elevated transition-all duration-300 hover:-translate-y-1 cursor-pointer group h-full">
                <CardHeader className="flex flex-col items-center text-center pb-2">
                  <div className={`w-16 h-16 rounded-xl ${option.gradient} flex items-center justify-center group-hover:scale-110 transition-transform mb-4`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  <CardTitle className="text-lg font-bold mb-2">
                    {option.title}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {option.description}
                  </p>
                </CardHeader>
              </Card>
            </Link>
          );
        })}
      </div>

      {/* Admin Stats (only if authenticated) */}
      {isAuthenticated && stats.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <Link key={index} to={stat.link}>
                  <Card className="glass-effect hover:shadow-elevated transition-all duration-300 hover:-translate-y-1 cursor-pointer group">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        {stat.title}
                      </CardTitle>
                      <div className={`w-12 h-12 rounded-xl ${stat.gradient} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">
                        {loadingCameras || loadingImages ? '...' : stat.value}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>

          {/* Recent Activity */}
          <Card className="glass-effect shadow-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-2xl">{t('dashboard.recentActivity')}</CardTitle>
                <Link to="/saved-images">
                  <Button variant="ghost" size="sm">
                    {t('dashboard.viewAll')}
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {loadingImages ? (
                <div className="text-center py-8 text-muted-foreground">
                  {t('common.loading')}
                </div>
              ) : todayImages?.items?.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  {todayImages.items.map((image: any) => (
                    <div
                      key={image.id}
                      className="aspect-square rounded-xl overflow-hidden shadow-card hover:shadow-elevated transition-all hover:scale-105"
                    >
                      <img
                        src={image.image_url}
                        alt="Captured face"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  {t('dashboard.noActivity')}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default Dashboard;
