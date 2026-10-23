; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c20402363_merge_or_split_occurred () Bool)
(declare-fun c20402363_owner_rewards_after_merge_split () Int)
(declare-fun c20402363_ve_nft_pending_rewards_before_merge_split () Int)
(assert
 (= c20402363_merge_or_split_occurred c20402363_merge_or_split_occurred))
(assert
 (= c20402363_owner_rewards_after_merge_split c20402363_owner_rewards_after_merge_split))
(assert
 (= c20402363_ve_nft_pending_rewards_before_merge_split c20402363_ve_nft_pending_rewards_before_merge_split))
(define-fun report_preconditions () Bool (< 0 c20402363_ve_nft_pending_rewards_before_merge_split))
(define-fun report_safety () Bool (=> c20402363_merge_or_split_occurred
    (=> c20402363_merge_or_split_occurred
        (= c20402363_owner_rewards_after_merge_split
           c20402363_ve_nft_pending_rewards_before_merge_split))))
(define-fun report_effects () Bool (and c20402363_merge_or_split_occurred
     c20402363_merge_or_split_occurred
     (not (= c20402363_owner_rewards_after_merge_split
             c20402363_ve_nft_pending_rewards_before_merge_split))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
