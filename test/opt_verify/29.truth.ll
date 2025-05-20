[INST]Optimize the following LLVM IR with O3:\n<code>declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #0
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #0
declare dso_local void @gdImageSetPixel(ptr noundef, i32 noundef, i32 noundef, i32 noundef) #1
define dso_local void @gdImageFilledRectangle(ptr noundef %0, i32 noundef %1, i32 noundef %2, i32 noundef %3, i32 noundef %4, i32 noundef %5) #1 {
B0:
%6 = alloca ptr, align 8
%7 = alloca i32, align 4
%8 = alloca i32, align 4
%9 = alloca i32, align 4
%10 = alloca i32, align 4
%11 = alloca i32, align 4
%12 = alloca i32, align 4
%13 = alloca i32, align 4
store ptr %0, ptr %6, align 8, !tbaa !5
store i32 %1, ptr %7, align 4, !tbaa !9
store i32 %2, ptr %8, align 4, !tbaa !9
store i32 %3, ptr %9, align 4, !tbaa !9
store i32 %4, ptr %10, align 4, !tbaa !9
store i32 %5, ptr %11, align 4, !tbaa !9
call void @llvm.lifetime.start.p0(i64 4, ptr %12) #2
call void @llvm.lifetime.start.p0(i64 4, ptr %13) #2
%14 = load i32, ptr %8, align 4, !tbaa !9
store i32 %14, ptr %13, align 4, !tbaa !9
br label %B1
B1:
%15 = load i32, ptr %13, align 4, !tbaa !9
%16 = load i32, ptr %10, align 4, !tbaa !9
%17 = icmp sle i32 %15, %16
br i1 %17, label %B2, label %B8
B2:
%18 = load i32, ptr %7, align 4, !tbaa !9
store i32 %18, ptr %12, align 4, !tbaa !9
br label %B3
B3:
%19 = load i32, ptr %12, align 4, !tbaa !9
%20 = load i32, ptr %9, align 4, !tbaa !9
%21 = icmp sle i32 %19, %20
br i1 %21, label %B4, label %B6
B4:
%22 = load ptr, ptr %6, align 8, !tbaa !5
%23 = load i32, ptr %12, align 4, !tbaa !9
%24 = load i32, ptr %13, align 4, !tbaa !9
%25 = load i32, ptr %11, align 4, !tbaa !9
call void @gdImageSetPixel(ptr noundef %22, i32 noundef %23, i32 noundef %24, i32 noundef %25)
br label %B5
B5:
%26 = load i32, ptr %12, align 4, !tbaa !9
%27 = add nsw i32 %26, 1
store i32 %27, ptr %12, align 4, !tbaa !9
br label %B3, !llvm.loop !11
B6:
br label %B7
B7:
%28 = load i32, ptr %13, align 4, !tbaa !9
%29 = add nsw i32 %28, 1
store i32 %29, ptr %13, align 4, !tbaa !9
br label %B1, !llvm.loop !13
B8:
call void @llvm.lifetime.end.p0(i64 4, ptr %13) #2
call void @llvm.lifetime.end.p0(i64 4, ptr %12) #2
ret void
}
attributes #0 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #1 = { nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { nounwind }
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
!11 = distinct !{!11, !12}
!12 = !{!"llvm.loop.mustprogress"}
!13 = distinct !{!13, !12}</code>[/INST]Opt IR:\n<code>\ndeclare dso_local void @gdImageSetPixel(ptr noundef, i32 noundef, i32 noundef, i32 noundef) local_unnamed_addr #0
define dso_local void @gdImageFilledRectangle(ptr noundef %0, i32 noundef %1, i32 noundef %2, i32 noundef %3, i32 noundef %4, i32 noundef %5) local_unnamed_addr #0 {
B0:
%6 = icmp sgt i32 %2, %4
%7 = icmp sgt i32 %1, %3
%8 = or i1 %6, %7
br i1 %8, label %B4, label %B1
B1:
%9 = phi i32 [ %13, %B3 ], [ %2, %B0 ]
br label %B2
B2:
%10 = phi i32 [ %1, %B1 ], [ %11, %B2 ]
tail call void @gdImageSetPixel(ptr noundef %0, i32 noundef %10, i32 noundef %9, i32 noundef %5)
%11 = add i32 %10, 1
%12 = icmp eq i32 %10, %3
br i1 %12, label %B3, label %B2, !llvm.loop !5
B3:
%13 = add i32 %9, 1
%14 = icmp eq i32 %9, %4
br i1 %14, label %B4, label %B1, !llvm.loop !7
B4:
ret void
}
attributes #0 = { nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
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