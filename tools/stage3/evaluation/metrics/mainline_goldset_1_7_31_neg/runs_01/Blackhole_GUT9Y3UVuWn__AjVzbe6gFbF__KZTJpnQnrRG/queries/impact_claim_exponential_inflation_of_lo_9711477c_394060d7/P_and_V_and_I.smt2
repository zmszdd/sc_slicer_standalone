; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cefdb1f93_locked_balance_inflated () Bool)
(declare-fun cefdb1f93_original_lock_is_sm_nft () Bool)
(declare-fun cefdb1f93_split_applies_bonus () Bool)
(assert
 (= cefdb1f93_locked_balance_inflated cefdb1f93_locked_balance_inflated))
(assert
 (= cefdb1f93_original_lock_is_sm_nft cefdb1f93_original_lock_is_sm_nft))
(assert
 (= cefdb1f93_split_applies_bonus cefdb1f93_split_applies_bonus))
(define-fun report_preconditions () Bool cefdb1f93_original_lock_is_sm_nft)
(define-fun report_safety () Bool (=> cefdb1f93_original_lock_is_sm_nft (not cefdb1f93_split_applies_bonus)))
(define-fun report_effects () Bool (and cefdb1f93_original_lock_is_sm_nft
     cefdb1f93_split_applies_bonus
     cefdb1f93_locked_balance_inflated))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
