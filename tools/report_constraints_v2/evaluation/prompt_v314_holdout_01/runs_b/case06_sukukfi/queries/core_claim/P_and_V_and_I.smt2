; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun claimable_deposit_assets () Int)
(declare-fun user_in_active_set () Bool)
(declare-fun second_request_initiated () Bool)
(declare-fun second_request_cancelled () Bool)
(declare-fun active_deposit_requesters_count () Int)
(assert
 (= claimable_deposit_assets claimable_deposit_assets))
(assert
 (= user_in_active_set user_in_active_set))
(assert
 (= second_request_initiated second_request_initiated))
(assert
 (= second_request_cancelled second_request_cancelled))
(assert
 (= active_deposit_requesters_count active_deposit_requesters_count))
(define-fun report_preconditions () Bool (and (< 0 claimable_deposit_assets)
     user_in_active_set
     second_request_initiated
     second_request_cancelled))
(define-fun report_safety () Bool (=> (< 0 claimable_deposit_assets) (= 1 active_deposit_requesters_count)))
(define-fun report_effects () Bool (and (< 0 claimable_deposit_assets) (not (= 1 active_deposit_requesters_count))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
