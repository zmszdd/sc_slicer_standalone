; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf910bd2_relayer_holds_op () Bool)
(declare-fun cbf910bd2_signed_op_valid () Bool)
(declare-fun cbf910bd2_suffix_excluded_from_hash () Bool)
(declare-fun cbf910bd2_unauthorized_wallet_actions () Bool)
(declare-fun cbf910bd2_window_authenticated () Bool)
(assert
 (= cbf910bd2_relayer_holds_op cbf910bd2_relayer_holds_op))
(assert
 (= cbf910bd2_signed_op_valid cbf910bd2_signed_op_valid))
(assert
 (= cbf910bd2_suffix_excluded_from_hash cbf910bd2_suffix_excluded_from_hash))
(assert
 (= cbf910bd2_unauthorized_wallet_actions cbf910bd2_unauthorized_wallet_actions))
(assert
 (= cbf910bd2_window_authenticated cbf910bd2_window_authenticated))
(define-fun report_preconditions () Bool (and cbf910bd2_signed_op_valid
     cbf910bd2_relayer_holds_op
     cbf910bd2_suffix_excluded_from_hash))
(define-fun report_safety () Bool (=> (and cbf910bd2_signed_op_valid
         cbf910bd2_relayer_holds_op
         cbf910bd2_suffix_excluded_from_hash)
    (and cbf910bd2_window_authenticated
         (not cbf910bd2_unauthorized_wallet_actions))))
(define-fun report_effects () Bool (and cbf910bd2_signed_op_valid
     cbf910bd2_relayer_holds_op
     cbf910bd2_suffix_excluded_from_hash
     (not (and cbf910bd2_window_authenticated
               (not cbf910bd2_unauthorized_wallet_actions)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
