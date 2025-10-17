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
    staleTime: 0, // No cache for testing
    gcTime: 0, // No cache for testing
    refetchInterval: 5000, // Refetch every 5 seconds for testing
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
    isPlanPackageEnabled: planPackageStatus?.is_enabled ?? false, // Default to disabled
  };
};
