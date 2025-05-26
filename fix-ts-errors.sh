#!/bin/bash

echo "Fixing TypeScript errors..."

# Fix AdminMonitoringPage.tsx - remove unused usageSummary
sed -i 's/const { usageSummary, isLoading, error } = useAdminMonitoring();/const { isLoading, error } = useAdminMonitoring();/' frontend/src/pages/Admin/AdminMonitoringPage.tsx

# Fix RegisterPage.tsx - remove unused navigate
sed -i '/const navigate = useNavigate();/d' frontend/src/pages/Auth/RegisterPage.tsx

# Fix ContestDetailPage.tsx - remove unused imports and variables
sed -i 's/, useNavigate//' frontend/src/pages/ContestDetail/ContestDetailPage.tsx
sed -i '/const navigate = useNavigate();/d' frontend/src/pages/ContestDetail/ContestDetailPage.tsx
sed -i '/interface ContestText {/,/}/d' frontend/src/pages/ContestDetail/ContestDetailPage.tsx
sed -i 's/const \[isFetching, setIsFetching\] = useState(false);//' frontend/src/pages/ContestDetail/ContestDetailPage.tsx
sed -i 's/const \[isLoadingJudgeAgents, setIsLoadingJudgeAgents\] = useState(false);//' frontend/src/pages/ContestDetail/ContestDetailPage.tsx

# Fix ContestListPage.tsx - remove unused imports and variables
sed -i 's/import { Link } from '\''react-router-dom'\'';//' frontend/src/pages/ContestList/ContestListPage.tsx
sed -i '/const emptyMessage = /d' frontend/src/pages/ContestList/ContestListPage.tsx

# Fix AIWriterPage.tsx - remove unused textId
sed -i 's/const { contestId, textId } = useParams<{ contestId: string; textId?: string }>();/const { contestId } = useParams<{ contestId: string }>();/' frontend/src/pages/Dashboard/AIWriterPage.tsx

# Fix DashboardPage.tsx - remove unused variables and functions
sed -i '/const navigate = useNavigate();/d' frontend/src/pages/Dashboard/DashboardPage.tsx
sed -i '/const \[errorSubmissions, setErrorSubmissions\] = useState<any\[\]>(\[\]);/d' frontend/src/pages/Dashboard/DashboardPage.tsx
sed -i '/const refreshUserData = async () => {/,/};/d' frontend/src/pages/Dashboard/DashboardPage.tsx
sed -i '/const handleOpenCreateTextModal = () => {/,/};/d' frontend/src/pages/Dashboard/DashboardPage.tsx
sed -i 's/const \[isCreatingNew, setIsCreatingNew\] = useState(false);//' frontend/src/pages/Dashboard/DashboardPage.tsx

echo "TypeScript errors fixed!" 