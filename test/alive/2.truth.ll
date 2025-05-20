[INST]Optimize the following LLVM IR with O3:\n<code>define dso_local noundef i32 @_Z13boundaryCheckiiii(i32 noundef %0, i32 noundef %1, i32 noundef %2, i32 noundef %3) #0 {
B0:
%4 = alloca i32, align 4
%5 = alloca i32, align 4
%6 = alloca i32, align 4
%7 = alloca i32, align 4
%8 = alloca i32, align 4
store i32 %0, ptr %5, align 4, !tbaa !5
store i32 %1, ptr %6, align 4, !tbaa !5
store i32 %2, ptr %7, align 4, !tbaa !5
store i32 %3, ptr %8, align 4, !tbaa !5
%9 = load i32, ptr %5, align 4, !tbaa !5
%10 = icmp sge i32 %9, 0
br i1 %10, label %B1, label %B5
B1:
%11 = load i32, ptr %6, align 4, !tbaa !5
%12 = icmp sge i32 %11, 0
br i1 %12, label %B2, label %B5
B2:
%13 = load i32, ptr %5, align 4, !tbaa !5
%14 = load i32, ptr %7, align 4, !tbaa !5
%15 = icmp slt i32 %13, %14
br i1 %15, label %B3, label %B5
B3:
%16 = load i32, ptr %6, align 4, !tbaa !5
%17 = load i32, ptr %8, align 4, !tbaa !5
%18 = icmp slt i32 %16, %17
br i1 %18, label %B4, label %B5
B4:
store i32 1, ptr %4, align 4
br label %B6
B5:
store i32 0, ptr %4, align 4
br label %B6
B6:
%19 = load i32, ptr %4, align 4
ret i32 %19
}
attributes #0 = { mustprogress nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
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
!8 = !{!"Simple C++ TBAA"}</code>[/INST]Opt IR:\n<code>\ndefine dso_local noundef range(i32 0, 2) i32 @_Z13boundaryCheckiiii(i32 noundef %0, i32 noundef %1, i32 noundef %2, i32 noundef %3) local_unnamed_addr #0 {
B0:
%4 = or i32 %1, %0
%5 = icmp sgt i32 %4, -1
%6 = icmp slt i32 %0, %2
%7 = and i1 %5, %6
%8 = icmp slt i32 %1, %3
%9 = and i1 %7, %8
%10 = zext i1 %9 to i32
ret i32 %10
}
attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(none) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}\n</code>