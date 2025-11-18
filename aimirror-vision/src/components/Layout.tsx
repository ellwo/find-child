import React, { useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard,
  Camera,
  Images,
  Search,
  Sun,
  Moon,
  Languages,
  LogOut,
  Settings,
  Bus,
  Users,
  GraduationCap,
  MapPin,
  UserCheck,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const { isAuthenticated, isAdmin, isParent, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const isRTL = i18n.language === 'ar';

  useEffect(() => {
    document.documentElement.setAttribute('dir', isRTL ? 'rtl' : 'ltr');
  }, [isRTL]);

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'ar' ? 'en' : 'ar');
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Public navigation items
  const publicNavItems = [
    // { path: '/', label: t('nav.dashboard'), icon: LayoutDashboard },
  ];

  // Admin navigation items
  const adminNavItems = [
    { path: '/admin/dashboard', label: 'لوحة التحكم', icon: LayoutDashboard },
    { path: '/admin/buses', label: 'الحافلات', icon: Bus },
    { path: '/admin/parents', label: 'أولياء الأمور', icon: Users },
    { path: '/admin/students', label: 'الطلاب', icon: GraduationCap },
    { path: '/admin/attendance', label: 'الحضور', icon: UserCheck },
    { path: '/admin/trackers', label: 'أجهزة التتبع', icon: MapPin },
    { path: '/admin/live-tracking', label: 'التتبع اللحظي', icon: MapPin },
    // { path: '/cameras', label: t('nav.cameras'), icon: Camera },
    // { path: '/saved-images', label: t('nav.savedImages'), icon: Images },
    // { path: '/search', label: t('nav.search'), icon: Search },
    { path: '/admin/settings', label: 'الإعدادات', icon: Settings },
  ];

  // Parent navigation items
  const parentNavItems = [
    { path: '/parent/dashboard', label: 'لوحة التحكم', icon: LayoutDashboard },
    // { path: '/cameras', label: t('nav.cameras'), icon: Camera },
    // { path: '/saved-images', label: t('nav.savedImages'), icon: Images },
    // { path: '/search', label: t('nav.search'), icon: Search },
  ];

  const navItems = isAdmin 
    ? adminNavItems 
    : isParent 
    ? parentNavItems 
    : publicNavItems;

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-effect border-b backdrop-blur-md bg-background/80">
        <div className="container mx-auto px-3 sm:px-4 lg:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-2 sm:gap-4">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 sm:gap-3 group flex-shrink-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-primary flex items-center justify-center glow-effect group-hover:scale-110 transition-transform">
                <Bus className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
              </div>
              <span className="text-base sm:text-lg lg:text-xl font-bold bg-gradient-primary bg-clip-text text-transparent hidden sm:inline-block">
                {t('appName')}
              </span>
              <span className="text-sm font-bold bg-gradient-primary bg-clip-text text-transparent sm:hidden">
                رحلة آمنة
              </span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden lg:flex items-center gap-1 xl:gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={isActive ? 'default' : 'ghost'}
                      size="sm"
                      className={cn(
                        'gap-1.5 xl:gap-2 text-xs xl:text-sm',
                        isActive && 'bg-gradient-primary text-primary-foreground'
                      )}
                    >
                      <Icon className="w-3.5 h-3.5 xl:w-4 xl:h-4" />
                      <span className="hidden xl:inline">{item.label}</span>
                    </Button>
                  </Link>
                );
              })}
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
              {!isAuthenticated && (
                <>
                  <Link to="/admin/login" className="hidden sm:block">
                    <Button variant="outline" size="sm" className="text-xs xl:text-sm">
                      <span className="hidden lg:inline">تسجيل دخول الإدارة</span>
                      <span className="lg:hidden">إدارة</span>
                    </Button>
                  </Link>
                  <Link to="/parent/login" className="hidden sm:block">
                    <Button variant="outline" size="sm" className="text-xs xl:text-sm">
                      <span className="hidden lg:inline">تسجيل دخول ولي الأمر</span>
                      <span className="lg:hidden">ولي أمر</span>
                    </Button>
                  </Link>
                </>
              )}
              {isAuthenticated && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="gap-1.5 text-xs xl:text-sm"
                >
                  <LogOut className="w-3.5 h-3.5 xl:w-4 xl:h-4" />
                  <span className="hidden sm:inline">تسجيل الخروج</span>
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                title={t('theme.toggle')}
                className="w-8 h-8 sm:w-9 sm:h-9"
              >
                {theme === 'light' ? (
                  <Moon className="w-4 h-4 sm:w-5 sm:h-5" />
                ) : (
                  <Sun className="w-4 h-4 sm:w-5 sm:h-5" />
                )}
              </Button>
            </div>
          </div>

          {/* Tablet/Mobile Navigation */}
          <nav className="lg:hidden flex gap-1.5 sm:gap-2 mt-3 sm:mt-4 overflow-x-auto pb-2 scrollbar-hide">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link key={item.path} to={item.path} className="flex-shrink-0">
                  <Button
                    variant={isActive ? 'default' : 'ghost'}
                    size="sm"
                    className={cn(
                      'gap-1.5 whitespace-nowrap text-xs sm:text-sm',
                      isActive && 'bg-gradient-primary text-primary-foreground'
                    )}
                  >
                    <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-3 sm:px-4 lg:px-6 py-4 sm:py-6 lg:py-8 animate-fade-in">
        {children}
      </main>

      {/* Floating Search Button (Mobile Only) - Only show for authenticated users */}
      {isAuthenticated && location.pathname !== '/search' && (
        <Link to="/search" className="lg:hidden">
          <Button
            size="lg"
            className="fixed bottom-4 sm:bottom-6 ltr:right-4 sm:ltr:right-6 rtl:left-4 sm:rtl:left-6 z-40 w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-gradient-primary shadow-elevated hover:shadow-glow transition-all duration-300 hover:scale-110 glow-effect p-0"
          >
            <Search className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
          </Button>
        </Link>
      )}
    </div>
  );
};

export default Layout;
