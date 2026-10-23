; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9b182c01_relayer_holds_op () Bool)
(declare-fun c9b182c01_suffix_excluded_from_hash () Bool)
(declare-fun c9b182c01_valid_signed_op_exists () Bool)
(declare-fun c9b182c01_window_enforced () Bool)
(assert
 (= c9b182c01_relayer_holds_op c9b182c01_relayer_holds_op))
(assert
 (= c9b182c01_suffix_excluded_from_hash c9b182c01_suffix_excluded_from_hash))
(assert
 (= c9b182c01_valid_signed_op_exists c9b182c01_valid_signed_op_exists))
(assert
 (= c9b182c01_window_enforced c9b182c01_window_enforced))
(define-fun report_preconditions () Bool (and c9b182c01_valid_signed_op_exists
     c9b182c01_relayer_holds_op
     c9b182c01_suffix_excluded_from_hash))
(define-fun report_safety () Bool (=> (and c9b182c01_valid_signed_op_exists
         c9b182c01_relayer_holds_op
         c9b182c01_suffix_excluded_from_hash)
    c9b182c01_window_enforced))
(define-fun report_effects () Bool (and c9b182c01_valid_signed_op_exists
     c9b182c01_relayer_holds_op
     c9b182c01_suffix_excluded_from_hash
     (not c9b182c01_window_enforced)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
