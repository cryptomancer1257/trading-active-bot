import { useQuery } from '@tanstack/react-query';

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
      const response = await fetch('/api/admin/feature-flags/public/plan-package-status');
      if (!response.ok) {
        throw new Error('Failed to fetch plan package status');
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (renamed from cacheTime in v5)
    refetchInterval: 60 * 1000, // Refetch every minute
    retry: 1, // Only retry once
    retryDelay: 1000, // Wait 1 second before retry
  });

  return {
    planPackageStatus,
    isLoadingPlanPackage,
    planPackageError,
    refetchPlanPackage,
    isPlanPackageEnabled: planPackageStatus?.is_enabled ?? true, // Default to enabled
  };
};
