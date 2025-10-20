import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface PlanPackageStatus {
  is_enabled: boolean;
  reason: string;
  disabled_until?: string;
}

export const useFeatureFlags = () => {
  const {
    data: planPackageStatus,
    isLoading: isLoadingPlanPackage,
    error: planPackageError,
    refetch: refetchPlanPackage
  } = useQuery<PlanPackageStatus>({
    queryKey: ['feature-flags', 'plan-package-status'],
    queryFn: async () => {
      const response = await api.get('/feature-flags/public/plan-package-status');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes cache
    gcTime: 10 * 60 * 1000, // 10 minutes garbage collection
    retry: 1, // Only retry once
    retryDelay: 1000, // Wait 1 second before retry
  });

  // Debug logging
  console.log('useFeatureFlags Debug:', {
    planPackageStatus,
    isLoadingPlanPackage,
    planPackageError,
    isEnabled: planPackageStatus?.is_enabled
  });

  return {
    planPackageStatus,
    isLoadingPlanPackage,
    planPackageError,
    refetchPlanPackage,
    isPlanPackageEnabled: planPackageStatus?.is_enabled ?? true, // Default to enabled
  };
};
