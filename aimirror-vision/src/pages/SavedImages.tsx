import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { getSavedImages, getCameras } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Images, ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import { format } from 'date-fns';
import { Badge } from '@/components/ui/badge';

const SavedImages: React.FC = () => {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    camera_ids: 'all',
  });
  const [appliedFilters, setAppliedFilters] = useState(filters);

  const { data: cameras } = useQuery({
    queryKey: ['cameras'],
    queryFn: getCameras,
  });

  const { data: imagesData, isLoading } = useQuery({
    queryKey: ['saved-images', page, appliedFilters],
    queryFn: () =>
      getSavedImages({
        page,
        page_size: 20,
        start_date: appliedFilters.start_date,
        end_date: appliedFilters.end_date,
        camera_ids: appliedFilters.camera_ids === 'all' ? '' : appliedFilters.camera_ids,
      }),
    retry: false,
  });

  const applyFilters = () => {
    setAppliedFilters(filters);
    setPage(1);
  };

  const resetFilters = () => {
    const emptyFilters = { start_date: '', end_date: '', camera_ids: 'all' };
    setFilters(emptyFilters);
    setAppliedFilters(emptyFilters);
    setPage(1);
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-accent flex items-center justify-center glow-effect">
          <Images className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">{t('savedImages.title')}</h1>
          <p className="text-muted-foreground">
            {imagesData?.total || 0} {t('savedImages.title')}
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card className="glass-effect shadow-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            {t('savedImages.filters')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                {t('savedImages.startDate')}
              </label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                {t('savedImages.endDate')}
              </label>
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                {t('savedImages.camera')}
              </label>
              <Select
                value={filters.camera_ids}
                onValueChange={(value) => setFilters({ ...filters, camera_ids: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('savedImages.allCameras')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t('savedImages.allCameras')}</SelectItem>
                  {cameras?.map((camera: any) => (
                    <SelectItem key={camera.id} value={camera.code}>
                      {camera.name || camera.code}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end gap-2">
              <Button onClick={applyFilters} className="bg-gradient-primary flex-1">
                {t('savedImages.apply')}
              </Button>
              <Button onClick={resetFilters} variant="outline">
                {t('savedImages.reset')}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Images Grid */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="text-xl text-muted-foreground">{t('common.loading')}</div>
        </div>
      ) : imagesData?.items?.length === 0 ? (
        <Card className="glass-effect shadow-card">
          <CardContent className="py-12 text-center">
            <Images className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <p className="text-xl text-muted-foreground">{t('savedImages.noImages')}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {imagesData?.items?.map((image: any) => (
              <Card
                key={image.id}
                className="glass-effect shadow-card hover:shadow-elevated transition-all duration-300 hover:-translate-y-1 overflow-hidden"
              >
                <div className="aspect-square overflow-hidden">
                  <img
                    src={image.image_url}
                    alt="Face capture"
                    className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                  />
                </div>
                <CardContent className="p-3 space-y-2">
                  <Badge variant="secondary" className="text-xs">
                    {image.camera_name || image.camera_id}
                  </Badge>
                  <p className="text-xs text-muted-foreground">
                    {format(new Date(image.timestamp), 'PPp')}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {imagesData && imagesData.total_pages > 1 && (
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm">
                {t('savedImages.page')} {page} {t('savedImages.of')} {imagesData.total_pages}
              </span>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setPage((p) => Math.min(imagesData.total_pages, p + 1))}
                disabled={page === imagesData.total_pages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SavedImages;
