<s> [INST]Optimize the following LLVM IR with O3:\n<code>@_fx_system_date = external global i32, align 4
define dso_local i32 @_fx_system_date_get(ptr noundef %0, ptr noundef %1, ptr noundef %2) #0 {
B0:
%3 = alloca ptr, align 8
%4 = alloca ptr, align 8
%5 = alloca ptr, align 8
%6 = alloca i32, align 4
store ptr %0, ptr %3, align 8, !tbaa !5
store ptr %1, ptr %4, align 8, !tbaa !5
store ptr %2, ptr %5, align 8, !tbaa !5
call void @llvm.lifetime.start.p0(i64 4, ptr %6) #2
%7 = load i32, ptr @_fx_system_date, align 4, !tbaa !9
store i32 %7, ptr %6, align 4, !tbaa !9
%8 = load ptr, ptr %3, align 8, !tbaa !5
%9 = icmp ne ptr %8, null
br i1 %9, label %B1, label %B2
B1:
%10 = load i32, ptr %6, align 4, !tbaa !9
%11 = lshr i32 %10, 9
%12 = and i32 %11, 127
%13 = add i32 %12, 1980
%14 = load ptr, ptr %3, align 8, !tbaa !5
store i32 %13, ptr %14, align 4, !tbaa !9
br label %B2
B2:
%15 = load ptr, ptr %4, align 8, !tbaa !5
%16 = icmp ne ptr %15, null
br i1 %16, label %B3, label %B4
B3:
%17 = load i32, ptr %6, align 4, !tbaa !9
%18 = lshr i32 %17, 5
%19 = and i32 %18, 15
%20 = load ptr, ptr %4, align 8, !tbaa !5
store i32 %19, ptr %20, align 4, !tbaa !9
br label %B4
B4:
%21 = load ptr, ptr %5, align 8, !tbaa !5
%22 = icmp ne ptr %21, null
br i1 %22, label %B5, label %B6
B5:
%23 = load i32, ptr %6, align 4, !tbaa !9
%24 = and i32 %23, 31
%25 = load ptr, ptr %5, align 8, !tbaa !5
store i32 %24, ptr %25, align 4, !tbaa !9
br label %B6
B6:
%26 = load ptr, ptr %3, align 8, !tbaa !5
%27 = icmp ne ptr %26, null
br i1 %27, label %B7, label %B10
B7:
%28 = load ptr, ptr %4, align 8, !tbaa !5
%29 = icmp ne ptr %28, null
br i1 %29, label %B8, label %B10
B8:
%30 = load ptr, ptr %5, align 8, !tbaa !5
%31 = icmp ne ptr %30, null
br i1 %31, label %B9, label %B10
B9:
br label %B10
B10:
call void @llvm.lifetime.end.p0(i64 4, ptr %6) #2
ret i32 0
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
!6 = !{!"any pointer", !7, i64 0}
!7 = !{!"omnipotent char", !8, i64 0}
!8 = !{!"Simple C/C++ TBAA"}
!9 = !{!10, !10, i64 0}
!10 = !{!"int", !7, i64 0}</code>[/INST]Opt IR:\n<code>\n@_fx_system_date = external local_unnamed_addr global i32, align 4
define dso_local noundef i32 @_fx_system_date_get(ptr noundef writeonly %0, ptr noundef writeonly %1, ptr noundef writeonly %2) local_unnamed_addr #0 {
B0:
%3 = load i32, ptr @_fx_system_date, align 4, !tbaa !5
%4 = icmp eq ptr %0, null
br i1 %4, label %B2, label %B1
B1:
%5 = lshr i32 %3, 9
%6 = and i32 %5, 127
%7 = add nuw nsw i32 %6, 1980
store i32 %7, ptr %0, align 4, !tbaa !5
%8 = icmp eq ptr %1, null
br i1 %8, label %B4, label %B3
B2:
%9 = icmp eq ptr %1, null
br i1 %9, label %B4, label %B3
B3:
%10 = lshr i32 %3, 5
%11 = and i32 %10, 15
store i32 %11, ptr %1, align 4, !tbaa !5
%12 = icmp eq ptr %2, null
br i1 %12, label %B5, label %B4
B4:
%13 = and i32 %3, 31
store i32 %13, ptr %2, align 4, !tbaa !5
br label %B5
B5:
ret i32 0
}
attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(read, argmem: write, inaccessiblemem: none) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
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
!8 = !{!"Simple C/C++ TBAA"}\n</code>
</s>