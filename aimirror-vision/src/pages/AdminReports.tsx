import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAllReports, getReport, updateReportStatus, getReportMatches } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { AlertCircle, FileText, ChevronLeft, ChevronRight, Eye, CheckCircle2, Clock, X } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from '@/hooks/use-toast';

const AdminReports: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const { data: reportsData, isLoading } = useQuery({
    queryKey: ['admin-reports', page, statusFilter],
    queryFn: () => getAllReports({ page, page_size: 20, status_filter: statusFilter || undefined }),
  });

  const { data: reportDetails } = useQuery({
    queryKey: ['admin-report', selectedReportId],
    queryFn: () => getReport(selectedReportId!),
    enabled: !!selectedReportId && showDetails,
  });

  const { data: reportMatches } = useQuery({
    queryKey: ['admin-report-matches', selectedReportId],
    queryFn: () => getReportMatches(selectedReportId!),
    enabled: !!selectedReportId && showDetails,
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ reportId, status }: { reportId: number; status: string }) =>
      updateReportStatus(reportId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-reports'] });
      queryClient.invalidateQueries({ queryKey: ['admin-report', selectedReportId] });
      toast({
        title: t('admin.success'),
        description: t('admin.statusUpdated'),
      });
    },
    onError: (error: any) => {
      toast({
        title: t('admin.error'),
        description: error?.response?.data?.detail || t('admin.updateFailed'),
        variant: 'destructive',
      });
    },
  });

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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open':
        return <AlertCircle className="w-4 h-4" />;
      case 'in_progress':
        return <Clock className="w-4 h-4" />;
      case 'resolved':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'closed':
        return <X className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  const handleViewDetails = (reportId: number) => {
    setSelectedReportId(reportId);
    setShowDetails(true);
  };

  const handleStatusChange = (reportId: number, newStatus: string) => {
    updateStatusMutation.mutate({ reportId, status: newStatus });
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-accent flex items-center justify-center glow-effect">
          <FileText className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">{t('admin.reports')}</h1>
          <p className="text-muted-foreground">{t('admin.manageReports')}</p>
        </div>
      </div>

      <Card className="glass-effect shadow-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{t('admin.filters')}</CardTitle>
            <Select value={statusFilter || "all"} onValueChange={(value) => setStatusFilter(value === "all" ? "" : value)}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder={t('admin.allStatuses')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('admin.allStatuses')}</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
      </Card>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="text-xl text-muted-foreground">{t('common.loading')}</div>
        </div>
      ) : reportsData?.items?.length === 0 ? (
        <Card className="glass-effect shadow-card">
          <CardContent className="py-12 text-center">
            <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <p className="text-xl text-muted-foreground">{t('admin.noReports')}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {reportsData?.items?.map((report: any) => (
              <Card key={report.id} className="glass-effect shadow-card">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold font-mono">
                          {report.report_number}
                        </h3>
                        <Badge className={getStatusColor(report.status)}>
                          <span className="flex items-center gap-1">
                            {getStatusIcon(report.status)}
                            {report.status}
                          </span>
                        </Badge>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">{t('admin.childName')}</p>
                          <p className="font-semibold">{report.child_name}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">{t('admin.reporter')}</p>
                          <p>{report.reporter_name}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">{t('admin.createdAt')}</p>
                          <p>{format(new Date(report.created_at), 'PPp')}</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewDetails(report.id)}
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        {t('admin.view')}
                      </Button>
                      {report.status !== 'closed' && (
                        <Select
                          value={report.status}
                          onValueChange={(value) => handleStatusChange(report.id, value)}
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="open">Open</SelectItem>
                            <SelectItem value="in_progress">In Progress</SelectItem>
                            <SelectItem value="resolved">Resolved</SelectItem>
                            <SelectItem value="closed">Closed</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {reportsData && reportsData.total_pages > 1 && (
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
                {t('admin.page')} {page} {t('admin.of')} {reportsData.total_pages}
              </span>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setPage((p) => Math.min(reportsData.total_pages, p + 1))}
                disabled={page === reportsData.total_pages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          )}
        </>
      )}

      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {reportDetails?.report_number} - {t('admin.details')}
            </DialogTitle>
          </DialogHeader>
          {reportDetails && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">{t('admin.childName')}</p>
                  <p className="font-semibold">{reportDetails.child_name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('admin.status')}</p>
                  <Badge className={getStatusColor(reportDetails.status)}>
                    {reportDetails.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('admin.reporterName')}</p>
                  <p>{reportDetails.reporter_name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('admin.reporterEmail')}</p>
                  <p>{reportDetails.reporter_email}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('admin.reporterPhone')}</p>
                  <p>{reportDetails.reporter_phone}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('admin.createdAt')}</p>
                  <p>{format(new Date(reportDetails.created_at), 'PPp')}</p>
                </div>
              </div>

              {reportDetails.child_photo_url && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">{t('admin.childPhoto')}</p>
                  <img
                    src={reportDetails.child_photo_url}
                    alt="Child"
                    className="w-full max-w-md rounded-lg border"
                  />
                </div>
              )}

              {reportMatches && reportMatches.length > 0 && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {t('admin.matches')} ({reportMatches.length})
                  </p>
                  <div className="space-y-2">
                    {reportMatches.map((match: any) => (
                      <div key={match.id} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold">
                            {t('admin.similarity')}: {(match.similarity_score * 100).toFixed(1)}%
                          </span>
                          <Badge variant="secondary">{match.camera_id}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {format(new Date(match.matched_at), 'PPp')}
                        </p>
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
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminReports;

