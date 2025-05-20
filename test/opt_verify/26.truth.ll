[INST]Optimize the following LLVM IR with O3:\n<code>%STRUCT0 = type { %STRUCT1 }
%STRUCT1 = type { %STRUCT2, [320 x i8] }
%STRUCT2 = type { %STRUCT4, i8, i8, i8, i8, %STRUCT3, %STRUCT4, ptr, ptr, %STRUCT3, %STRUCT3, %STRUCT4, %STRUCT4, ptr, i32 }
%STRUCT3 = type { i32 }
%STRUCT4 = type { i32 }
%STRUCT5 = type { i64 }
%STRUCT2.1 = type { %STRUCT1.2, i32 }
%STRUCT1.2 = type { %STRUCT4 }
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #0
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #0
declare hidden ptr @lj_lib_checkstr(ptr noundef, i32 noundef) #1
define hidden ptr @lj_lib_optstr(ptr noundef %0, i32 noundef %1) #1 {
B0:
%2 = alloca ptr, align 8
%3 = alloca i32, align 4
%4 = alloca ptr, align 8
store ptr %0, ptr %2, align 8, !tbaa !5
store i32 %1, ptr %3, align 4, !tbaa !9
call void @llvm.lifetime.start.p0(i64 8, ptr %4) #2
%5 = load ptr, ptr %2, align 8, !tbaa !5
%6 = getelementptr inbounds %STRUCT0, ptr %5, i32 0, i32 0
%7 = getelementptr inbounds %STRUCT2, ptr %6, i32 0, i32 7
%8 = load ptr, ptr %7, align 8, !tbaa !11
%9 = load i32, ptr %3, align 4, !tbaa !9
%10 = sext i32 %9 to i64
%11 = getelementptr inbounds %STRUCT5, ptr %8, i64 %10
%12 = getelementptr inbounds %STRUCT5, ptr %11, i64 -1
store ptr %12, ptr %4, align 8, !tbaa !5
%13 = load ptr, ptr %4, align 8, !tbaa !5
%14 = load ptr, ptr %2, align 8, !tbaa !5
%15 = getelementptr inbounds %STRUCT0, ptr %14, i32 0, i32 0
%16 = getelementptr inbounds %STRUCT2, ptr %15, i32 0, i32 8
%17 = load ptr, ptr %16, align 8, !tbaa !11
%18 = icmp ult ptr %13, %17
br i1 %18, label %B1, label %B3
B1:
%19 = load ptr, ptr %4, align 8, !tbaa !5
%20 = getelementptr inbounds %STRUCT2.1, ptr %19, i32 0, i32 1
%21 = load i32, ptr %20, align 4, !tbaa !11
%22 = icmp eq i32 %21, -1
br i1 %22, label %B3, label %B2
B2:
%23 = load ptr, ptr %2, align 8, !tbaa !5
%24 = load i32, ptr %3, align 4, !tbaa !9
%25 = call ptr @lj_lib_checkstr(ptr noundef %23, i32 noundef %24)
br label %B4
B3:
br label %B4
B4:
%26 = phi ptr [ %25, %B2 ], [ null, %B3 ]
call void @llvm.lifetime.end.p0(i64 8, ptr %4) #2
ret ptr %26
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
!11 = !{!7, !7, i64 0}</code>[/INST]Opt IR:\n<code>\n%STRUCT0 = type { i64 }
declare hidden ptr @lj_lib_checkstr(ptr noundef, i32 noundef) local_unnamed_addr #0
define hidden ptr @lj_lib_optstr(ptr noundef %0, i32 noundef %1) local_unnamed_addr #0 {
B0:
%2 = getelementptr inbounds i8, ptr %0, i64 16
%3 = load ptr, ptr %2, align 8, !tbaa !5
%4 = sext i32 %1 to i64
%5 = getelementptr inbounds %STRUCT0, ptr %3, i64 %4
%6 = getelementptr inbounds i8, ptr %5, i64 -8
%7 = getelementptr inbounds i8, ptr %0, i64 24
%8 = load ptr, ptr %7, align 8, !tbaa !5
%9 = icmp ult ptr %6, %8
br i1 %9, label %B1, label %B3
B1:
%10 = getelementptr inbounds i8, ptr %5, i64 -4
%11 = load i32, ptr %10, align 4, !tbaa !5
%12 = icmp eq i32 %11, -1
br i1 %12, label %B3, label %B2
B2:
%13 = tail call ptr @lj_lib_checkstr(ptr noundef nonnull %0, i32 noundef %1)
br label %B3
B3:
%14 = phi ptr [ %13, %B2 ], [ null, %B1 ], [ null, %B0 ]
ret ptr %14
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
!6 = !{!"omnipotent char", !7, i64 0}
!7 = !{!"Simple C/C++ TBAA"}\n</code>