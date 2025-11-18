import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { trackReport, closeReport } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Search, AlertCircle, CheckCircle2, X, Loader2, MapPin, Clock } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { format } from 'date-fns';

const TrackReport: React.FC = () => {
  const { t } = useTranslation();
  const [phone, setPhone] = useState('');
  const [reportNumber, setReportNumber] = useState('');

  const trackMutation = useMutation({
    mutationFn: () => trackReport(phone, reportNumber),
    onError: (error: any) => {
      const errorMessage =
        error?.response?.data?.detail || t('track.error');
      toast({
        title: t('track.error'),
        description: errorMessage,
        variant: 'destructive',
      });
    },
  });

  const closeMutation = useMutation({
    mutationFn: () => closeReport(reportNumber, phone),
    onSuccess: () => {
      toast({
        title: t('track.success'),
        description: t('track.reportClosed'),
      });
      trackMutation.mutate();
    },
    onError: (error: any) => {
      const errorMessage =
        error?.response?.data?.detail || t('track.closeError');
      toast({
        title: t('track.closeError'),
        description: errorMessage,
        variant: 'destructive',
      });
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone || !reportNumber) {
      toast({
        title: t('track.error'),
        description: t('track.fillAllFields'),
        variant: 'destructive',
      });
      return;
    }
    trackMutation.mutate();
  };

  const handleClose = () => {
    if (window.confirm(t('track.confirmClose'))) {
      closeMutation.mutate();
    }
  };

  const report = trackMutation.data?.report;
  const matches = trackMutation.data?.matches || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-blue-500';
      case 'in_progress':
        return 'bg-yellow-500';
      case 'resolved':
        return 'bg-green-500';
      case 'closed':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-accent flex items-center justify-center glow-effect">
          <Search className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">{t('track.title')}</h1>
          <p className="text-muted-foreground">{t('track.description')}</p>
        </div>
      </div>

      <Card className="glass-effect shadow-card">
        <CardHeader>
          <CardTitle>{t('track.searchForm')}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="phone">{t('track.phone')} *</Label>
              <Input
                id="phone"
                type="tel"
                placeholder={t('track.phonePlaceholder')}
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="report_number">{t('track.reportNumber')} *</Label>
              <Input
                id="report_number"
                type="text"
                placeholder="REP-2025-0001"
                value={reportNumber}
                onChange={(e) => setReportNumber(e.target.value.toUpperCase())}
                required
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-gradient-primary"
              disabled={trackMutation.isPending}
            >
              {trackMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('track.searching')}
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  {t('track.search')}
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {trackMutation.isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {t('track.notFound')}
          </AlertDescription>
        </Alert>
      )}

      {report && (
        <div className="space-y-4">
          <Card className="glass-effect shadow-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{t('track.reportDetails')}</CardTitle>
                <Badge className={getStatusColor(report.status)}>
                  {report.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">{t('track.reportNumber')}</p>
                  <p className="font-mono font-bold">{report.report_number}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('track.childName')}</p>
                  <p className="font-semibold">{report.child_name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('track.reporterName')}</p>
                  <p>{report.reporter_name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('track.createdAt')}</p>
                  <p>{format(new Date(report.created_at), 'PPp')}</p>
                </div>
              </div>

              {report.child_photo_url && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">{t('track.childPhoto')}</p>
                  <img
                    src={report.child_photo_url}
                    alt="Child"
                    className="w-full max-w-md rounded-lg border"
                  />
                </div>
              )}

              {report.status !== 'closed' && (
                <Button
                  onClick={handleClose}
                  variant="destructive"
                  disabled={closeMutation.isPending}
                >
                  {closeMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {t('track.closing')}
                    </>
                  ) : (
                    <>
                      <X className="mr-2 h-4 w-4" />
                      {t('track.closeReport')}
                    </>
                  )}
                </Button>
              )}
            </CardContent>
          </Card>

          {matches.length > 0 && (
            <Card className="glass-effect shadow-card">
              <CardHeader>
                <CardTitle>{t('track.matches')} ({matches.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {matches.map((match: any) => (
                    <div
                      key={match.id}
                      className="border rounded-lg p-4 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-5 h-5 text-green-500" />
                          <span className="font-semibold">
                            {t('track.similarity')}: {(match.similarity_score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Badge variant="secondary">
                          {match.camera_id}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {format(new Date(match.matched_at), 'PPp')}
                        </div>
                        {match.camera_name && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            {match.camera_name}
                          </div>
                        )}
                      </div>
                      {match.image_url && (
                        <img
                          src={match.image_url}
                          alt="Match"
                          className="w-full max-w-md rounded-lg border mt-2"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default TrackReport;

