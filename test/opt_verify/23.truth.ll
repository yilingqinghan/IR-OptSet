[INST]Optimize the following LLVM IR with O3:\n<code>define dso_local i32 @ft_tolower(i32 noundef %0) #0 {
B0:
%1 = alloca i32, align 4
store i32 %0, ptr %1, align 4, !tbaa !5
%2 = load i32, ptr %1, align 4, !tbaa !5
%3 = icmp sge i32 %2, 65
br i1 %3, label %B1, label %B3
B1:
%4 = load i32, ptr %1, align 4, !tbaa !5
%5 = icmp sle i32 %4, 90
br i1 %5, label %B2, label %B3
B2:
%6 = load i32, ptr %1, align 4, !tbaa !5
%7 = add nsw i32 %6, 32
br label %B4
B3:
%8 = load i32, ptr %1, align 4, !tbaa !5
br label %B4
B4:
%9 = phi i32 [ %7, %B2 ], [ %8, %B3 ]
ret i32 %9
}
attributes #0 = { nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}
!5 = !{!6, !6, i64 0}
!6 = !{!"int", !7, i64 0}
!7 = !{!"omnipotent char", !8, i64 0}
!8 = !{!"Simple C/C++ TBAA"}</code>[/INST]Opt IR:\n<code>\ndefine dso_local i32 @ft_tolower(i32 noundef %0) local_unnamed_addr #0 {
B0:
%1 = add i32 %0, -65
%2 = icmp ult i32 %1, 26
%3 = add nuw nsw i32 %0, 32
%4 = select i1 %2, i32 %3, i32 %0
ret i32 %4
}
attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}\n</code>