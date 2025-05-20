<s> [INST]Optimize the following LLVM IR with O3:\n<code>define dso_local i32 @get_divisor(i32 noundef %0) #0 {
B0:
%1 = alloca i32, align 4
%2 = alloca i32, align 4
%3 = alloca i32, align 4
store i32 %0, ptr %1, align 4, !tbaa !5
call void @llvm.lifetime.start.p0(i64 4, ptr %2) #2
store i32 1, ptr %2, align 4, !tbaa !5
call void @llvm.lifetime.start.p0(i64 4, ptr %3) #2
%4 = load i32, ptr %1, align 4, !tbaa !5
store i32 %4, ptr %3, align 4, !tbaa !5
br label %B1
B1:
%5 = load i32, ptr %1, align 4, !tbaa !5
%6 = icmp sgt i32 %5, 0
br i1 %6, label %B2, label %B3
B2:
%7 = load i32, ptr %1, align 4, !tbaa !5
%8 = sdiv i32 %7, 10
store i32 %8, ptr %1, align 4, !tbaa !5
%9 = load i32, ptr %2, align 4, !tbaa !5
%10 = mul nsw i32 %9, 10
store i32 %10, ptr %2, align 4, !tbaa !5
br label %B1, !llvm.loop !9
B3:
%11 = load i32, ptr %3, align 4, !tbaa !5
%12 = icmp eq i32 %11, 0
br i1 %12, label %B4, label %B5
B4:
br label %B6
B5:
%13 = load i32, ptr %2, align 4, !tbaa !5
br label %B6
B6:
%14 = phi i32 [ 1, %B4 ], [ %13, %B5 ]
call void @llvm.lifetime.end.p0(i64 4, ptr %3) #2
call void @llvm.lifetime.end.p0(i64 4, ptr %2) #2
ret i32 %14
}
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #1
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #1
attributes #0 = { nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #2 = { nounwind }
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
!8 = !{!"Simple C/C++ TBAA"}
!9 = distinct !{!9, !10}
!10 = !{!"llvm.loop.mustprogress"}</code>[/INST]Opt IR:\n<code>\ndefine dso_local i32 @get_divisor(i32 noundef %0) local_unnamed_addr #0 {
B0:
%1 = icmp sgt i32 %0, 0
br i1 %1, label %B1, label %B2
B1:
%2 = phi i32 [ %4, %B1 ], [ 1, %B0 ]
%3 = phi i32 [ %5, %B1 ], [ %0, %B0 ]
%4 = mul nuw nsw i32 %2, 10
%5 = udiv i32 %3, 10
%6 = icmp ult disjoint i32 %3, 10
br i1 %6, label %B2, label %B1, !llvm.loop !5
B2:
%7 = phi i32 [ 1, %B0 ], [ %4, %B1 ]
%8 = icmp eq i32 %0, 0
%9 = select i1 %8, i32 1, i32 %7
ret i32 %9
}
attributes #0 = { nofree norecurse nosync nounwind memory(none) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}
!5 = distinct !{!5, !6}
!6 = !{!"llvm.loop.mustprogress"}\n</code>
</s>