; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun parent_amount () Int)
(declare-fun child_amount_sum () Int)
(declare-fun parent_is_permanent () Bool)
(declare-fun child_count () Int)
(declare-fun parent_amount_not_divisible () Bool)
(assert
 (= parent_amount parent_amount))
(assert
 (= child_amount_sum child_amount_sum))
(assert
 (= parent_is_permanent parent_is_permanent))
(assert
 (= child_count child_count))
(assert
 (= parent_amount_not_divisible parent_amount_not_divisible))
(define-fun report_preconditions () Bool (and parent_is_permanent (<= 2 child_count) parent_amount_not_divisible))
(define-fun report_safety () Bool (=> (and parent_is_permanent (<= 2 child_count))
    (= child_amount_sum parent_amount)))
(define-fun report_effects () Bool (and parent_is_permanent
     (<= 2 child_count)
     (not (= child_amount_sum parent_amount))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
