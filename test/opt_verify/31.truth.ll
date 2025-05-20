[INST]Optimize the following LLVM IR with O3:\n<code>declare dso_local ptr @__kmpc_impl_malloc(i64 noundef) #0
declare dso_local void @__kmpc_impl_free(ptr noundef) #0
define dso_local noundef i32 @main() #1 {
B0:
%0 = alloca i32, align 4
%1 = alloca ptr, align 8
%2 = alloca i32, align 4
store i32 0, ptr %0, align 4
call void @llvm.lifetime.start.p0(i64 8, ptr %1) #3
%3 = call ptr @__kmpc_impl_malloc(i64 noundef 128)
store ptr %3, ptr %1, align 8, !tbaa !5
call void @llvm.lifetime.start.p0(i64 4, ptr %2) #3
store i32 0, ptr %2, align 4, !tbaa !9
br label %B1
B1:
%4 = load i32, ptr %2, align 4, !tbaa !9
%5 = icmp ult i32 %4, 128
br i1 %5, label %B3, label %B2
B2:
call void @llvm.lifetime.end.p0(i64 4, ptr %2) #3
br label %B5
B3:
%6 = load i32, ptr %2, align 4, !tbaa !9
%7 = trunc i32 %6 to i8
%8 = load ptr, ptr %1, align 8, !tbaa !5
store i8 %7, ptr %8, align 1, !tbaa !11
br label %B4
B4:
%9 = load i32, ptr %2, align 4, !tbaa !9
%10 = add i32 %9, 1
store i32 %10, ptr %2, align 4, !tbaa !9
br label %B1, !llvm.loop !12
B5:
%11 = load ptr, ptr %1, align 8, !tbaa !5
call void @__kmpc_impl_free(ptr noundef %11)
call void @llvm.lifetime.end.p0(i64 8, ptr %1) #3
ret i32 0
}
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #2
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #2
attributes #0 = { mustprogress uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { mustprogress norecurse uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
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
!8 = !{!"Simple C++ TBAA"}
!9 = !{!10, !10, i64 0}
!10 = !{!"int", !7, i64 0}
!11 = !{!7, !7, i64 0}
!12 = distinct !{!12, !13}
!13 = !{!"llvm.loop.mustprogress"}</code>[/INST]Opt IR:\n<code>\ndeclare dso_local ptr @__kmpc_impl_malloc(i64 noundef) local_unnamed_addr #0
declare dso_local void @__kmpc_impl_free(ptr noundef) local_unnamed_addr #0
define dso_local noundef i32 @main() local_unnamed_addr #1 {
B0:
%0 = tail call ptr @__kmpc_impl_malloc(i64 noundef 128)
store i8 127, ptr %0, align 1, !tbaa !5
tail call void @__kmpc_impl_free(ptr noundef nonnull %0)
ret i32 0
}
attributes #0 = { mustprogress uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { mustprogress norecurse uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}
!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 19.1.0 (git@github.com:llvm/llvm-project.git a4bf6cd7cfb1a1421ba92bca9d017b49936c55e4)"}
!5 = !{!6, !6, i64 0}
!6 = !{!"omnipotent char", !7, i64 0}
!7 = !{!"Simple C++ TBAA"}\n</code>