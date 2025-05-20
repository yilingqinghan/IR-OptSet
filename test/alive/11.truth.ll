[INST]Optimize the following LLVM IR with O3:\n<code>define dso_local noundef zeroext i1 @_Z9is_triplei(i32 noundef %0) #0 {
B0:
%1 = alloca i32, align 4
%2 = alloca i32, align 4
store i32 %0, ptr %1, align 4, !tbaa !5
call void @llvm.lifetime.start.p0(i64 4, ptr %2) #3
%3 = load i32, ptr %1, align 4, !tbaa !5
%4 = sitofp i32 %3 to double
%5 = call double @sqrt(double noundef %4) #3
%6 = fptosi double %5 to i32
store i32 %6, ptr %2, align 4, !tbaa !5
br label %B1
B1:
%7 = load i32, ptr %2, align 4, !tbaa !5
%8 = add nsw i32 %7, 1
%9 = load i32, ptr %2, align 4, !tbaa !5
%10 = add nsw i32 %9, 2
%11 = mul nsw i32 %8, %10
%12 = ashr i32 %11, 1
%13 = load i32, ptr %1, align 4, !tbaa !5
%14 = icmp sle i32 %12, %13
br i1 %14, label %B2, label %B4
B2:
br label %B3
B3:
%15 = load i32, ptr %2, align 4, !tbaa !5
%16 = add nsw i32 %15, 1
store i32 %16, ptr %2, align 4, !tbaa !5
br label %B1, !llvm.loop !9
B4:
br label %B5
B5:
%17 = load i32, ptr %2, align 4, !tbaa !5
%18 = load i32, ptr %2, align 4, !tbaa !5
%19 = add nsw i32 %18, 1
%20 = mul nsw i32 %17, %19
%21 = ashr i32 %20, 1
%22 = load i32, ptr %1, align 4, !tbaa !5
%23 = icmp sgt i32 %21, %22
br i1 %23, label %B6, label %B8
B6:
br label %B7
B7:
%24 = load i32, ptr %2, align 4, !tbaa !5
%25 = add nsw i32 %24, -1
store i32 %25, ptr %2, align 4, !tbaa !5
br label %B5, !llvm.loop !11
B8:
%26 = load i32, ptr %2, align 4, !tbaa !5
%27 = load i32, ptr %2, align 4, !tbaa !5
%28 = add nsw i32 %27, 1
%29 = mul nsw i32 %26, %28
%30 = ashr i32 %29, 1
%31 = load i32, ptr %1, align 4, !tbaa !5
%32 = icmp eq i32 %30, %31
call void @llvm.lifetime.end.p0(i64 4, ptr %2) #3
ret i1 %32
}
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #1
declare double @sqrt(double noundef) #2
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #1
attributes #0 = { mustprogress nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #2 = { nounwind "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { nounwind }
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
!8 = !{!"Simple C++ TBAA"}
!9 = distinct !{!9, !10}
!10 = !{!"llvm.loop.mustprogress"}
!11 = distinct !{!11, !10}</code>[/INST]Opt IR:\n<code>\ndefine dso_local noundef zeroext i1 @_Z9is_triplei(i32 noundef %0) local_unnamed_addr #0 {
B0:
%1 = sitofp i32 %0 to double
%2 = tail call double @sqrt(double noundef %1) #2
%3 = fptosi double %2 to i32
br label %B1
B1:
%4 = phi i32 [ %3, %B0 ], [ %5, %B1 ]
%5 = add nsw i32 %4, 1
%6 = add nsw i32 %4, 2
%7 = mul nsw i32 %5, %6
%8 = ashr i32 %7, 1
%9 = icmp sgt i32 %8, %0
br i1 %9, label %B2, label %B1, !llvm.loop !5
B2:
%10 = phi i32 [ %15, %B2 ], [ %4, %B1 ]
%11 = add nsw i32 %10, 1
%12 = mul nsw i32 %11, %10
%13 = ashr i32 %12, 1
%14 = icmp sgt i32 %13, %0
%15 = add nsw i32 %10, -1
br i1 %14, label %B2, label %B3, !llvm.loop !7
B3:
%16 = icmp eq i32 %13, %0
ret i1 %16
}
declare double @sqrt(double noundef) local_unnamed_addr #1
attributes #0 = { mustprogress nofree nounwind memory(write) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { mustprogress nofree nounwind willreturn memory(write) "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { nounwind }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}
!5 = distinct !{!5, !6}
!6 = !{!"llvm.loop.mustprogress"}
!7 = distinct !{!7, !6}\n</code>