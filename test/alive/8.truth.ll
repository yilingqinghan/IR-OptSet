[INST]Optimize the following LLVM IR with O3:\n<code>%STRUCT0 = type { i32, i32 }
define dso_local i64 @mulpt(i64 %0, i64 %1) #0 {
B0:
%2 = alloca %STRUCT0, align 4
%3 = alloca %STRUCT0, align 4
%4 = alloca %STRUCT0, align 4
store i64 %0, ptr %3, align 4
store i64 %1, ptr %4, align 4
%5 = getelementptr inbounds %STRUCT0, ptr %4, i32 0, i32 0
%6 = load i32, ptr %5, align 4, !tbaa !5
%7 = getelementptr inbounds %STRUCT0, ptr %3, i32 0, i32 0
%8 = load i32, ptr %7, align 4, !tbaa !5
%9 = mul nsw i32 %8, %6
store i32 %9, ptr %7, align 4, !tbaa !5
%10 = getelementptr inbounds %STRUCT0, ptr %4, i32 0, i32 1
%11 = load i32, ptr %10, align 4, !tbaa !10
%12 = getelementptr inbounds %STRUCT0, ptr %3, i32 0, i32 1
%13 = load i32, ptr %12, align 4, !tbaa !10
%14 = mul nsw i32 %13, %11
store i32 %14, ptr %12, align 4, !tbaa !10
call void @llvm.memcpy.p0.p0.i64(ptr align 4 %2, ptr align 4 %3, i64 8, i1 false), !tbaa.struct !11
%15 = load i64, ptr %2, align 4
ret i64 %15
}
declare void @llvm.memcpy.p0.p0.i64(ptr noalias nocapture writeonly, ptr noalias nocapture readonly, i64, i1 immarg) #1
attributes #0 = { nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nocallback nofree nounwind willreturn memory(argmem: readwrite) }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}
!5 = !{!6, !7, i64 0}
!6 = !{!"Point", !7, i64 0, !7, i64 4}
!7 = !{!"int", !8, i64 0}
!8 = !{!"omnipotent char", !9, i64 0}
!9 = !{!"Simple C/C++ TBAA"}
!10 = !{!6, !7, i64 4}
!11 = !{i64 0, i64 4, !12, i64 4, i64 4, !12}
!12 = !{!7, !7, i64 0}</code>[/INST]Opt IR:\n<code>\ndefine dso_local i64 @mulpt(i64 %0, i64 %1) local_unnamed_addr #0 {
B0:
%2 = and i64 %0, -4294967296
%3 = lshr i64 %1, 32
%4 = mul i64 %1, %0
%5 = mul i64 %2, %3
%6 = and i64 %4, 4294967295
%7 = or disjoint i64 %5, %6
ret i64 %7
}
attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}\n</code>