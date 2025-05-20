[INST]Optimize the following LLVM IR with O3:\n<code>define dso_local void @arm_add_q15(ptr noundef %0, ptr noundef %1, ptr noundef %2, i32 noundef %3) #0 {
B0:
%4 = alloca ptr, align 8
%5 = alloca ptr, align 8
%6 = alloca ptr, align 8
%7 = alloca i32, align 4
%8 = alloca i32, align 4
store ptr %0, ptr %4, align 8, !tbaa !5
store ptr %1, ptr %5, align 8, !tbaa !5
store ptr %2, ptr %6, align 8, !tbaa !5
store i32 %3, ptr %7, align 4, !tbaa !9
call void @llvm.lifetime.start.p0(i64 4, ptr %8) #3
%9 = load i32, ptr %7, align 4, !tbaa !9
store i32 %9, ptr %8, align 4, !tbaa !9
br label %B1
B1:
%10 = load i32, ptr %8, align 4, !tbaa !9
%11 = icmp ugt i32 %10, 0
br i1 %11, label %B2, label %B3
B2:
%12 = load ptr, ptr %4, align 8, !tbaa !5
%13 = getelementptr inbounds i16, ptr %12, i32 1
store ptr %13, ptr %4, align 8, !tbaa !5
%14 = load i16, ptr %12, align 2, !tbaa !11
%15 = sext i16 %14 to i32
%16 = load ptr, ptr %5, align 8, !tbaa !5
%17 = getelementptr inbounds i16, ptr %16, i32 1
store ptr %17, ptr %5, align 8, !tbaa !5
%18 = load i16, ptr %16, align 2, !tbaa !11
%19 = sext i16 %18 to i32
%20 = add nsw i32 %15, %19
%21 = call i32 @__SSAT(i32 noundef %20, i32 noundef 16)
%22 = trunc i32 %21 to i16
%23 = load ptr, ptr %6, align 8, !tbaa !5
%24 = getelementptr inbounds i16, ptr %23, i32 1
store ptr %24, ptr %6, align 8, !tbaa !5
store i16 %22, ptr %23, align 2, !tbaa !11
%25 = load i32, ptr %8, align 4, !tbaa !9
%26 = add i32 %25, -1
store i32 %26, ptr %8, align 4, !tbaa !9
br label %B1, !llvm.loop !13
B3:
call void @llvm.lifetime.end.p0(i64 4, ptr %8) #3
ret void
}
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #1
declare hidden i32 @__SSAT(i32 noundef, i32 noundef) #2
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #1
attributes #0 = { nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #2 = { alwaysinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { nounwind }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}
!5 = !{!6, !6, i64 0}
!6 = !{!"any pointer", !7, i64 0}
!7 = !{!"omnipotent char", !8, i64 0}
!8 = !{!"Simple C/C++ TBAA"}
!9 = !{!10, !10, i64 0}
!10 = !{!"int", !7, i64 0}
!11 = !{!12, !12, i64 0}
!12 = !{!"short", !7, i64 0}
!13 = distinct !{!13, !14}
!14 = !{!"llvm.loop.mustprogress"}</code>[/INST]Opt IR:\n<code>\ndefine dso_local void @arm_add_q15(ptr nocapture noundef readonly %0, ptr nocapture noundef readonly %1, ptr nocapture noundef writeonly %2, i32 noundef %3) local_unnamed_addr #0 {
B0:
%4 = icmp eq i32 %3, 0
br i1 %4, label %B2, label %B1
B1:
%5 = phi i32 [ %19, %B1 ], [ %3, %B0 ]
%6 = phi ptr [ %9, %B1 ], [ %0, %B0 ]
%7 = phi ptr [ %18, %B1 ], [ %2, %B0 ]
%8 = phi ptr [ %12, %B1 ], [ %1, %B0 ]
%9 = getelementptr inbounds i8, ptr %6, i64 2
%10 = load i16, ptr %6, align 2, !tbaa !5
%11 = sext i16 %10 to i32
%12 = getelementptr inbounds i8, ptr %8, i64 2
%13 = load i16, ptr %8, align 2, !tbaa !5
%14 = sext i16 %13 to i32
%15 = add nsw i32 %14, %11
%16 = tail call i32 @__SSAT(i32 noundef %15, i32 noundef 16)
%17 = trunc i32 %16 to i16
%18 = getelementptr inbounds i8, ptr %7, i64 2
store i16 %17, ptr %7, align 2, !tbaa !5
%19 = add i32 %5, -1
%20 = icmp eq i32 %19, 0
br i1 %20, label %B2, label %B1, !llvm.loop !9
B2:
ret void
}
declare hidden i32 @__SSAT(i32 noundef, i32 noundef) local_unnamed_addr #1
attributes #0 = { nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { alwaysinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}
!5 = !{!6, !6, i64 0}
!6 = !{!"short", !7, i64 0}
!7 = !{!"omnipotent char", !8, i64 0}
!8 = !{!"Simple C/C++ TBAA"}
!9 = distinct !{!9, !10}
!10 = !{!"llvm.loop.mustprogress"}\n</code>