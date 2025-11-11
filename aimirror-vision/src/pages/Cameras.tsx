import React from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { getCameras } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Camera, Clock, Image } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';

const Cameras: React.FC = () => {
  const { t } = useTranslation();

  const { data: cameras, isLoading } = useQuery({
    queryKey: ['cameras'],
    queryFn: getCameras,
  });

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="text-xl text-muted-foreground">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center glow-effect">
          <Camera className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">{t('cameras.title')}</h1>
          <p className="text-muted-foreground">
            {cameras?.length || 0} {t('cameras.title')}
          </p>
        </div>
      </div>

      {cameras?.length === 0 ? (
        <Card className="glass-effect shadow-card">
          <CardContent className="py-12 text-center">
            <Camera className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <p className="text-xl text-muted-foreground">{t('cameras.noCameras')}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cameras?.map((camera: any) => {
            const isActive = camera.last_seen
              ? new Date(camera.last_seen).getTime() > Date.now() - 24 * 60 * 60 * 1000
              : false;

            return (
              <Card
                key={camera.id}
                className="glass-effect shadow-card hover:shadow-elevated transition-all duration-300 hover:-translate-y-1"
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center">
                        <Camera className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{camera.name || camera.code}</CardTitle>
                        <p className="text-sm text-muted-foreground">{camera.code}</p>
                      </div>
                    </div>
                    <Badge variant={isActive ? 'default' : 'secondary'}>
                      {isActive ? t('cameras.active') : t('cameras.inactive')}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Image className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground">{t('cameras.totalImages')}:</span>
                    <span className="font-semibold">{camera.total_images}</span>
                  </div>
                  {camera.first_seen && (
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span className="text-muted-foreground">{t('cameras.firstSeen')}:</span>
                      <span className="font-medium">
                        {format(new Date(camera.first_seen), 'PPp')}
                      </span>
                    </div>
                  )}
                  {camera.last_seen && (
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span className="text-muted-foreground">{t('cameras.lastSeen')}:</span>
                      <span className="font-medium">
                        {format(new Date(camera.last_seen), 'PPp')}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Cameras;
