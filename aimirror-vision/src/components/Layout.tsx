import React, { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard,
  Camera,
  Images,
  Search,
  Sun,
  Moon,
  Languages,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const isRTL = i18n.language === 'ar';
  const token = localStorage.getItem('token');
  const isAuthenticated = !!token;

  useEffect(() => {
    document.documentElement.setAttribute('dir', isRTL ? 'rtl' : 'ltr');
  }, [isRTL]);

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'ar' ? 'en' : 'ar');
  };

  // Public navigation items (always visible)
  const publicNavItems = [
    { path: '/', label: t('nav.dashboard'), icon: LayoutDashboard },
    { path: '/search', label: t('nav.search'), icon: Search },
    { path: '/report', label: t('nav.reportMissing'), icon: AlertCircle },
    { path: '/track', label: t('nav.trackReport'), icon: FileText },
  ];

  // Protected navigation items (only visible when authenticated)
  const protectedNavItems = [
    { path: '/cameras', label: t('nav.cameras'), icon: Camera },
    { path: '/saved-images', label: t('nav.savedImages'), icon: Images },
    { path: '/admin/reports', label: t('nav.adminReports'), icon: FileText },
  ];

  // Combine navigation items based on authentication
  const navItems = [
    ...publicNavItems,
    ...(isAuthenticated ? protectedNavItems : []),
  ];

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-effect border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center glow-effect group-hover:scale-110 transition-transform">
                <Camera className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                {t('appName')}
              </span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={isActive ? 'default' : 'ghost'}
                      className={cn(
                        'gap-2',
                        isActive && 'bg-gradient-primary text-primary-foreground'
                      )}
                    >
                      <Icon className="w-4 h-4" />
                      {item.label}
                    </Button>
                  </Link>
                );
              })}
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleLanguage}
                title={i18n.language === 'ar' ? 'English' : 'العربية'}
              >
                <Languages className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                title={t('theme.toggle')}
              >
                {theme === 'light' ? (
                  <Moon className="w-5 h-5" />
                ) : (
                  <Sun className="w-5 h-5" />
                )}
              </Button>
            </div>
          </div>

          {/* Mobile Navigation */}
          <nav className="md:hidden flex gap-2 mt-4 overflow-x-auto pb-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link key={item.path} to={item.path}>
                  <Button
                    variant={isActive ? 'default' : 'ghost'}
                    size="sm"
                    className={cn(
                      'gap-2 whitespace-nowrap',
                      isActive && 'bg-gradient-primary text-primary-foreground'
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 animate-fade-in">
        {children}
      </main>

      {/* Floating Search Button (Mobile Only) */}
      {location.pathname !== '/search' && (
        <Link to="/search" className="md:hidden">
          <Button
            size="lg"
            className="fixed bottom-6 ltr:right-6 rtl:left-6 z-40 w-14 h-14 rounded-full bg-gradient-primary shadow-elevated hover:shadow-glow transition-all duration-300 hover:scale-110 glow-effect p-0"
          >
            <Search className="w-6 h-6 text-white" />
          </Button>
        </Link>
      )}
    </div>
  );
};

export default Layout;
