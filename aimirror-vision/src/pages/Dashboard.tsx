import React from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { getCameras, getSavedImages } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Camera, Images, Activity, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();

  const { data: cameras, isLoading: loadingCameras } = useQuery({
    queryKey: ['cameras'],
    queryFn: getCameras,
  });

  const { data: todayImages, isLoading: loadingImages } = useQuery({
    queryKey: ['today-images'],
    queryFn: () => getSavedImages({ page_size: 5 }),
  });

  const stats = [
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
  ];

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

      {/* Stats Grid */}
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
    </div>
  );
};

export default Dashboard;
